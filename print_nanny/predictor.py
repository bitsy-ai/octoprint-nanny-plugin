import base64
import datetime
import io
import threading
import json
import logging
import numpy as np
import os
from PIL import Image as PImage
import tensorflow as tf
import requests
import queue
from time import sleep


from print_nanny.utils.visualization import visualize_boxes_and_labels_on_image_array

# python 3.8
try:
    from typing import TypedDict, Optional

# python 3.7
except:
    from typing_extensions import TypedDict
    from typing import Optional

logger = logging.getLogger("octoprint.plugins.print_nanny")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s  - %(name)s - %(levelname)s - %(message)s [%(process)d - %(threadName)s]")
handler.setFormatter(formatter)

class Prediction(TypedDict):
    num_detections: int
    detection_scores: np.ndarray
    detection_boxes: np.ndarray
    detection_classes: np.ndarray
    viz: Optional[PImage.Image]


class Calibration(TypedDict):
    x0: np.float32
    y0: np.float32
    x1: np.float32
    y1: np.float32


class ThreadLocalPredictor(threading.local):
    base_path = os.path.join(os.path.dirname(__file__), "data")

    def __init__(
        self,
        min_score_thresh=0.50,
        max_boxes_to_draw=10,
        min_overlap_area=0.66,
        calibration = None,
        model_version="tflite-print3d-2020-10-23T18:00:41.136Z",
        model_filename="model.tflite",
        metadata_filename="tflite_metadata.json",
        label_filename="dict.txt",
        *args,
        **kwargs
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

        self.tflite_interpreter = tf.lite.Interpreter(model_path=self.model_path)
        self.tflite_interpreter.allocate_tensors()
        self.input_details = self.tflite_interpreter.get_input_details()
        self.output_details = self.tflite_interpreter.get_output_details()
        self.min_score_thresh = min_score_thresh
        self.max_boxes_to_draw = max_boxes_to_draw
        self.min_overlap_area = min_overlap_area
        self.__dict__.update(**kwargs)

        with open(self.metadata_path) as f:
            self.metadata = json.load(f)

        with open(self.label_path) as f:
            self.category_index = [l.strip() for l in f.readlines()]
            self.category_index = {
                i: {"name": v, "id": i} for i, v in enumerate(self.category_index)
            }
            print(self.category_index)
        self.input_shape = self.metadata["inputShape"]

        self.calibration = self.calibration

    def load_url_buffer(self, url: str):
        res = requests.get(url)
        res.raise_for_status()
        assert res.headers["content-type"] == "image/jpeg"
        return io.BytesIO(res.content)

    def load_image(self, bytes):
        return PImage.open(bytes)

    def load_file(self, filepath: str):
        return PImage.open(filepath)

    def preprocess(self, image: PImage):
        image = np.asarray(image)
        image = tf.convert_to_tensor(image, dtype=tf.uint8)
        image = tf.image.resize(image, self.input_shape[1:-1], method="nearest")
        image = image[tf.newaxis, ...]
        return image

    def write_image(self, outfile: str, image_np: np.ndarray):

        img = PImage.fromarray(image_np)
        img.save(outfile)

    def percent_intersection(
        self, detection_boxes, detection_scores, detection_classes, bb1
    ):
        """
        bb1 - boundary box
        bb2 - detection box
        """
        aou = np.zeros(len(detection_boxes))

        for i, bb2 in enumerate(detection_boxes):

            # assert bb1[0] < bb1[2]
            # assert bb1[1] < bb1[3]
            # assert bb2[0] < bb2[2]
            # assert bfrom datetime import datetime
b2[1] < bb2[3]

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

    def postprocess(self, image: PImage, prediction: Prediction):

        image_np = np.asarray(image).copy()
        height, width, _ = image_np.shape

        if self.calibration is not None:
            detection_boundary_mask = calibration["mask"]
            coords = calibration["coords"]
            percent_intersection = self.percent_intersection(
                prediction["detection_boxes"],
                prediction["detection_scores"],
                prediction["detection_classes"],
                coords,
            )
            ignored_mask = percent_intersection <= self.min_overlap_area

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
        return viz

    def predict(self, image: PImage) -> Prediction:
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

        logger.info(num_detections)

        return Prediction(
            detection_boxes=box_data,
            detection_classes=class_data,
            detection_scores=score_data,
            num_detections=num_detections,
        )


class PredictWorker:

    PREDICT_DONE = "predict_done"

    def __init__(self, webcam_url, web_queue, websocket_queue, calibration, fps=5):

        self.calibration = calibration
        self._fps = fps
        self._webcam_url = webcam_url
        self._task_queue = queue.Queue(maxsize=20)
        
        self._web_queue = web_queue
        self._websocket_queue = websocket_queue

        self._predictor = ThreadLocalPredictor(calibration=calibration)

        self._producer_thread = threading.Thread(target=self._producer, daemon=True, name='producer')
        self._producer_thread.start()

        self._consumer_thread = threading.Thread(target=self._consumer, daemon=True, name='consumer')
        self._consumer_thread.start()

    def _producer(self):
        '''
            Samples frame buffer from webcam stream
        '''
        logger.info('Started PredictWorker.producer thread')
        while True:
            try:
                now = datetime.now()
                self._task_queue.put_nowait({
                'ts': now
                'image_buffer': self._predictor.load_url_buffer(self._webcam_url)
                })
            except Queue.Full:
                logger.warning(f'Predict queue full, skipping frame @ ts: {now}')
            time.sleep(self.fps / 1000)

    def _consumer(self):
        '''
            Calculates prediction and publishes result to subscriber queues
        '''
        logger.info('Started PredictWorker.consumer thread')

        while True:
            
            msg = self._task_queue.get(block=True)

            msg['image_buffer'].name = "original_image.jpg"
            image = self._predictor.load_image(msg['image_buffer'])
            prediction = self._predictor.predict(image)

            viz_np = self._predictor.postprocess(
                image, prediction
            )
            viz_image = Image.fromarray(viz_np, "RGB")
            viz_buffer = io.BytesIO()
            viz_buffer.name = "annotated_image.jpg"
            viz_image.save(viz_buffer, format="JPEG")
            viz_bytes = viz_buffer.getvalue()
            
            self._web_queue.put(viz_bytes)
            self._websocket_queue.put({
                'original_image': original_image,
                'annotated_image': viz_buffer,
                'prediction': prediction
            })
            self._task_queue.done()


