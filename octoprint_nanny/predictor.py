import base64
import json
import logging
import numpy as np
import pandas as pd
import os
import time
import io
import threading
from dataclasses import asdict

import PIL
import tflite_runtime.interpreter as tflite

from octoprint_nanny.utils.visualization import (
    visualize_boxes_and_labels_on_image_array,
)
import octoprint_nanny.types
import beeline

from typing import Optional, Tuple

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.predictor")

DETECTION_LABELS = {
    1: "nozzle",
    2: "adhesion",
    3: "spaghetti",
    4: "print",
    5: "raft",
}

NEUTRAL_LABELS = {1: "nozzle", 5: "raft"}

NEGATIVE_LABELS = {
    2: "adhesion",
    3: "spaghetti",
}

POSITIVE_LABELS = {
    4: "print",
}


class ThreadLocalPredictor(threading.local):
    base_path = os.path.join(os.path.dirname(__file__), "data")

    def __init__(
        self,
        min_score_thresh: float = 0.50,
        max_boxes_to_draw: int = 10,
        min_overlap_area: float = 0.75,
        calibration: dict = None,
        model_version: str = "tflite-print3d-2020-10-23T18:00:41.136Z",
        model_filename: str = "model.tflite",
        metadata_filename: str = "tflite_metadata.json",
        label_filename: str = "dict.txt",
        *args,
        **kwargs,
    ):

        self.model_version = model_version
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        self.label_filename = label_filename

        self.model_path = os.path.join(self.base_path, model_version, model_filename)
        self.label_path = os.path.join(self.base_path, model_version, label_filename)
        self.metadata_path = os.path.join(
            self.base_path, model_version, metadata_filename
        )

        self.tflite_interpreter = tflite.Interpreter(model_path=self.model_path)
        self.tflite_interpreter.allocate_tensors()
        self.input_details = self.tflite_interpreter.get_input_details()
        self.output_details = self.tflite_interpreter.get_output_details()
        self.min_score_thresh = min_score_thresh
        self.max_boxes_to_draw = max_boxes_to_draw
        self.min_overlap_area = min_overlap_area
        self.__dict__.update(**kwargs)

        with open(self.metadata_path) as f:
            self.metadata = json.load(f)

        self.input_shape = self.metadata["inputShape"]

        with open(self.label_path) as f:
            self.category_index = [l.strip() for l in f.readlines()]
            self.category_index = {
                i: {"name": v, "id": i} for i, v in enumerate(self.category_index)
            }
        self.input_shape = self.metadata["inputShape"]

        self.calibration = calibration

    def load_image(self, image_bytes):
        return PIL.Image.open(io.BytesIO(image_bytes))

    def load_file(self, filepath: str):
        return PIL.Image.open(filepath)

    def preprocess(self, image: PIL.Image):
        # resize to input shape provided by model metadata.json
        _, target_height, target_width, _ = self.input_shape
        image = image.resize((target_width, target_height), resample=PIL.Image.BILINEAR)
        image = np.asarray(image)
        # expand dimensions to batch size = 1
        image = np.expand_dims(image, 0)
        return image

    def write_image(self, outfile: str, image_np: np.ndarray):
        img = PIL.Image.fromarray(image_np)
        return img.save(outfile)

    def percent_intersection(
        self,
        prediction: octoprint_nanny.types.BoundingBoxPrediction,
        area_of_interest: np,
    ) -> float:
        """
        Returns intersection-over-union area, normalized between 0 and 1
        """

        detection_boxes = prediction.detection_boxes
        # initialize array of zeroes
        aou = np.zeros(len(detection_boxes))

        # for each bounding box, calculate the intersection-over-area
        for i, box in enumerate(detection_boxes):
            # determine the coordinates of the intersection rectangle
            x_left = max(area_of_interest[0], box[0])
            y_top = max(area_of_interest[1], box[1])
            x_right = min(area_of_interest[2], box[2])
            y_bottom = min(area_of_interest[3], box[3])

            # boxes do not intersect, area is 0
            if x_right < x_left or y_bottom < y_top:
                aou[i] = 0.0
                continue

            # calculate
            # The intersection of two axis-aligned bounding boxes is always an
            # axis-aligned bounding box
            intersection_area = (x_right - x_left) * (y_bottom - y_top)

            # compute the area of detection box
            box_area = (box[2] - box[0]) * (box[3] - box[1])

            if (intersection_area / box_area) == 1.0:
                aou[i] = 1.0
                continue

            aou[i] = intersection_area / box_area

        return aou

    def postprocess(
        self, image: PIL.Image, prediction: octoprint_nanny.types.BoundingBoxPrediction
    ) -> np.array:

        image_np = np.asarray(image).copy()
        height, width, _ = image_np.shape
        ignored_mask = None

        prediction = self.min_score_filter(prediction)
        if prediction is None:
            logger.info(
                f"No detections exceeding min_score_thresh={self.min_score_thresh}"
            )
            return prediction, None
        if self.calibration is not None:
            detection_boundary_mask = self.calibration["mask"]
            prediction, ignored_mask = self.calibration_filter(prediction)

            viz = visualize_boxes_and_labels_on_image_array(
                image_np,
                prediction.detection_boxes,
                prediction.detection_classes,
                prediction.detection_scores,
                self.category_index,
                use_normalized_coordinates=True,
                line_thickness=4,
                min_score_thresh=self.min_score_thresh,
                max_boxes_to_draw=self.max_boxes_to_draw,
                detection_boundary_mask=detection_boundary_mask,
                detection_box_ignored=ignored_mask,
            )
        else:
            viz = visualize_boxes_and_labels_on_image_array(
                image_np,
                prediction.detection_boxes,
                prediction.detection_classes,
                prediction.detection_scores,
                self.category_index,
                use_normalized_coordinates=True,
                line_thickness=4,
                min_score_thresh=self.min_score_thresh,
                max_boxes_to_draw=self.max_boxes_to_draw,
            )
        return prediction, viz

    def min_score_filter(
        self, prediction: octoprint_nanny.types.BoundingBoxPrediction
    ) -> octoprint_nanny.types.BoundingBoxPrediction:
        ma = np.ma.masked_greater(prediction.detection_scores, self.min_score_thresh)
        # No detections exceeding threshold
        if isinstance(ma.mask, np.bool_) and ma.mask == False:
            return
        num_detections = int(np.count_nonzero(ma.mask))
        detection_boxes = prediction.detection_boxes[ma.mask]
        detection_classes = prediction.detection_classes[ma.mask]
        detection_scores = prediction.detection_scores[ma.mask]
        return octoprint_nanny.types.BoundingBoxPrediction(
            detection_boxes=detection_boxes,
            detection_classes=detection_classes,
            detection_scores=detection_scores,
            num_detections=num_detections,
        )

    def calibration_filter(
        self, prediction: octoprint_nanny.types.BoundingBoxPrediction
    ) -> octoprint_nanny.types.BoundingBoxPrediction:
        if self.calibration is not None:
            coords = self.calibration["coords"]
            percent_intersection = self.percent_intersection(prediction, coords)
            ignored_mask = percent_intersection <= self.min_overlap_area

            included_mask = np.invert(ignored_mask)
            detection_boxes = np.squeeze(prediction.detection_boxes[included_mask])
            detection_scores = np.squeeze(prediction.detection_scores[included_mask])
            detection_classes = np.squeeze(prediction.detection_classes[included_mask])

            num_detections = int(np.count_nonzero(included_mask))

            return (
                octoprint_nanny.types.BoundingBoxPrediction(
                    detection_boxes=detection_boxes,
                    detection_scores=detection_scores,
                    detection_classes=detection_classes,
                    num_detections=num_detections,
                ),
                ignored_mask,
            )
        return prediction, None

    def predict(self, image: PIL.Image) -> octoprint_nanny.types.BoundingBoxPrediction:
        tensor = self.preprocess(image)

        self.tflite_interpreter.set_tensor(self.input_details[0]["index"], tensor)
        self.tflite_interpreter.invoke()

        box_data = self.tflite_interpreter.get_tensor(self.output_details[0]["index"])

        class_data = self.tflite_interpreter.get_tensor(self.output_details[1]["index"])
        score_data = self.tflite_interpreter.get_tensor(self.output_details[2]["index"])
        num_detections = self.tflite_interpreter.get_tensor(
            self.output_details[3]["index"]
        )

        class_data = np.squeeze(class_data, axis=0).astype(np.int64) + 1
        box_data = np.squeeze(box_data, axis=0)
        score_data = np.squeeze(score_data, axis=0)
        num_detections = np.squeeze(num_detections, axis=0)

        return octoprint_nanny.types.BoundingBoxPrediction(
            detection_boxes=box_data,
            detection_classes=class_data,
            detection_scores=score_data,
            num_detections=num_detections,
        )


PREDICTOR = None


def explode_prediction_df(
    ts: int, prediction: octoprint_nanny.types.BoundingBoxPrediction
) -> pd.DataFrame:

    data = {"frame_id": ts, **asdict(prediction)}
    df = pd.DataFrame.from_records([data])

    df = df[["frame_id", "detection_classes", "detection_scores"]]
    df = df.reset_index()

    NUM_FRAMES = len(df)

    # explode nested detection_scores and detection_classes series
    df = df.set_index(["frame_id"]).apply(pd.Series.explode).reset_index()
    assert len(df) == NUM_FRAMES * prediction.num_detections

    # add string labels
    df["label"] = df["detection_classes"].map(DETECTION_LABELS)

    # create a hierarchal index from exploded data, append to dataframe state
    return df.set_index(["frame_id", "label"])


def print_is_healthy(df: pd.DataFrame, degree: int = 1) -> float:
    if df.empty:
        return True
    df = pd.concat(
        {
            "unhealthy": df[df["detection_classes"].isin(NEGATIVE_LABELS)],
            "healthy": df[df["detection_classes"].isin(POSITIVE_LABELS)],
        }
    ).reset_index()

    mask = df.level_0 == "unhealthy"
    healthy_cumsum = np.log10(
        df[~mask].groupby("frame_id")["detection_scores"].sum().cumsum()
    )

    unhealthy_cumsum = np.log10(
        df[mask].groupby("frame_id")["detection_scores"].sum().cumsum()
    )

    xy = healthy_cumsum.subtract(unhealthy_cumsum, fill_value=0)

    if len(xy) == 1:
        return True

    trend = np.polynomial.polynomial.Polynomial.fit(xy.index, xy, degree)
    slope, intercept = list(trend)
    if slope < 0:
        return False
    return True


def predict_threadsafe(
    image_bytes: bytes, **kwargs
) -> Tuple[
    octoprint_nanny.types.Image,
    Optional[octoprint_nanny.types.Image],
    Optional[octoprint_nanny.types.BoundingBoxPrediction],
]:

    global PREDICTOR
    if PREDICTOR is None:
        PREDICTOR = ThreadLocalPredictor(**kwargs)
    image = PREDICTOR.load_image(image_bytes)
    # NOTE: PIL.Image.size returns (w, h) where most TensorFlow interfaces expect (h, w)
    (ow, oh) = image.size
    original_frame = octoprint_nanny.types.Image(height=oh, width=ow, data=image_bytes)

    prediction = PREDICTOR.predict(image)

    prediction, viz_np = PREDICTOR.postprocess(image, prediction)
    if viz_np is not None:
        viz_image = PIL.Image.fromarray(viz_np, "RGB")
        vw, vh = viz_image.size
        viz_buffer = io.BytesIO()
        viz_buffer.name = "annotated_image.jpg"
        viz_image.save(viz_buffer, format="JPEG")

        post_frame = octoprint_nanny.types.Image(
            height=vh, width=vw, data=viz_buffer.getvalue()
        )
    else:
        post_frame = None

    return (
        original_frame,
        post_frame,
        prediction,
    )
