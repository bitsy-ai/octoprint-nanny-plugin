import base64
import json
import logging
import numpy as np
import os
import time
import threading

import PIL
import tflite_runtime.interpreter as tflite

from octoprint_nanny.utils.visualization import (
    visualize_boxes_and_labels_on_image_array,
)

# python >= 3.8
try:
    from typing import TypedDict, Optional
# python <= 3.7
except:
    from typing_extensions import TypedDict
    from typing import Optional

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.predictor")


class Prediction(TypedDict):
    image: PIL.Image.Image
    num_detections: int
    detection_scores: np.ndarray
    detection_boxes: np.ndarray
    detection_classes: np.ndarray


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

    def load_image(self, bytes):
        return PIL.Image.open(bytes)

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
        img.save(outfile)

    def percent_intersection(
        self,
        prediction: Prediction,
        bb1: tuple,
    ) -> float:
        """
        bb1 - boundary box
        bb2 - detection box
        """
        detection_boxes = prediction["detection_boxes"]
        detection_scores = (prediction["detection_scores"],)
        detection_classes = prediction["detection_classes"]

        aou = np.zeros(len(detection_boxes))

        for i, bb2 in enumerate(detection_boxes):

            # assert bb1[0] < bb1[2]
            # assert bb1[1] < bb1[3]
            # assert bb2[0] < bb2[2]
            # assert bb2[1] < bb2[3]

            # determine the coordinates of the intersection rectangle
            x_left = max(bb1[0], bb2[0])
            y_top = max(bb1[1], bb2[1])
            x_right = min(bb1[2], bb2[2])
            y_bottom = min(bb1[3], bb2[3])

            # boxes do not intersect
            if x_right < x_left or y_bottom < y_top:
                aou[i] = 0.0
                continue
            # The intersection of two axis-aligned bounding boxes is always an
            # axis-aligned bounding box
            intersection_area = (x_right - x_left) * (y_bottom - y_top)

            # compute the area of detection box
            bb2_area = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])

            if (intersection_area / bb2_area) == 1.0:
                aou[i] = 1.0
                continue

            aou[i] = intersection_area / bb2_area

        return aou

    def postprocess(self, image: PIL.Image, prediction: Prediction) -> np.array:

        image_np = np.asarray(image).copy()
        height, width, _ = image_np.shape
        ignored_mask = None

        prediction = self.min_score_filter(prediction)

        if self.calibration is not None:
            detection_boundary_mask = self.calibration["mask"]
            prediction, ignored_mask = self.calibration_filter(prediction)

            viz = visualize_boxes_and_labels_on_image_array(
                image_np,
                prediction["detection_boxes"],
                prediction["detection_classes"],
                prediction["detection_scores"],
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
                prediction["detection_boxes"],
                prediction["detection_classes"],
                prediction["detection_scores"],
                self.category_index,
                use_normalized_coordinates=True,
                line_thickness=4,
                min_score_thresh=self.min_score_thresh,
                max_boxes_to_draw=self.max_boxes_to_draw,
            )
        return prediction, viz

    def min_score_filter(self, prediction: Prediction) -> Prediction:
        ma = np.ma.masked_greater(prediction["detection_scores"], self.min_score_thresh)
        num_detections = np.count_nonzero(ma.mask)
        return Prediction(
            image_tensor=prediction["image_tensor"],
            detection_boxes=prediction["detection_boxes"][ma.mask],
            detection_classes=prediction["detection_classes"][ma.mask],
            detection_scores=prediction["detection_scores"][ma.mask],
            num_detections=num_detections,
        )

    def calibration_filter(self, prediction: Prediction) -> Prediction:
        if self.calibration is not None:
            coords = self.calibration["coords"]
            percent_intersection = self.percent_intersection(prediction, coords)
            ignored_mask = percent_intersection <= self.min_overlap_area

            included_mask = np.invert(ignored_mask)
            num_detections = np.count_nonzero(included_mask)
            return (
                Prediction(
                    image_tensor=prediction["image_tensor"],
                    detection_boxes=prediction["detection_boxes"][included_mask],
                    detection_scores=prediction["detection_scores"][included_mask],
                    detection_classes=prediction["detection_classes"][included_mask],
                    num_detections=num_detections,
                ),
                ignored_mask,
            )
        return prediction, None

    def predict(self, image: PIL.Image) -> Prediction:
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

        return Prediction(
            image_tensor=tensor,
            detection_boxes=box_data,
            detection_classes=class_data,
            detection_scores=score_data,
            num_detections=num_detections,
        )
