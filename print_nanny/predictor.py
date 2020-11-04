
import threading
import json
import numpy as np
import os
from PIL import Image as PImage
from typing import TypedDict, Optional
from print_nanny.utils.visualization import visualize_boxes_and_labels_on_image_array

import tensorflow as tf

class Prediction(TypedDict):
    num_detections: int
    detection_scores: np.ndarray
    detection_boxes: np.ndarray
    detection_classes: np.ndarray
    viz: Optional[PImage.Image]


class ThreadLocalPredictor(threading.local):
    base_path = os.path.join(os.path.dirname(__file__), 'data') 

    def __init__(self, 
        min_score_thresh=0.5, 
        max_boxes_to_draw=10, 
        model_version='tflite-print3d-2020-10-23T18:00:41.136Z',
        model_filename='model.tflite',
        metadata_filename='tflite_metadata.json',
        label_filename='dict.txt',

        
        *args, **kwargs
        ):

        self.model_version = model_version
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        self.label_filename = label_filename

        self.model_path = os.path.join(self.base_path, model_version, model_filename)
        self.label_path = os.path.join(self.base_path, model_version, label_filename)
        self.metadata_path = os.path.join(self.base_path, model_version, metadata_filename)

        self.tflite_interpreter = tf.lite.Interpreter(
            model_path=self.model_path
        )
        self.tflite_interpreter.allocate_tensors()
        self.input_details = self.tflite_interpreter.get_input_details()
        self.output_details = self.tflite_interpreter.get_output_details()
        self.min_score_thresh = min_score_thresh
        self.max_boxes_to_draw = max_boxes_to_draw
        self.__dict__.update(**kwargs)

        with open(self.metadata_path) as f:
            self.metadata = json.load(f)
        
        with open(self.label_path) as f:
            self.category_index = [l.strip() for l in f.readlines()]
            self.category_index = {i:{'name': v, 'id': i } for i, v in enumerate(self.category_index)}
            print(self.category_index)
        self.input_shape = self.metadata["inputShape"]

    def load_image(self, filepath: str):
        return PImage.open(filepath)
    
    def preprocess(self, image: PImage):
        image = np.asarray(image)
        image = tf.convert_to_tensor(image, dtype=tf.uint8)
        image = tf.image.resize(
            image,
            self.input_shape[1:-1],
            method='nearest'
        )
        image = image[tf.newaxis, ...]
        return image
    
    def write_image(self, outfile: str, image_np: np.ndarray):

        img = PImage.fromarray(image_np)
        img.save(outfile)

    def postprocess(self, image: PImage, prediction: Prediction) -> Prediction:

        image_np = np.asarray(image).copy()
        prediction = prediction.copy()

        prediction['viz'] = visualize_boxes_and_labels_on_image_array(
            image_np,
            prediction['detection_boxes'],
            prediction['detection_classes'],
            prediction['detection_scores'],
            self.category_index,
            use_normalized_coordinates=True,
            line_thickness=4,
            min_score_thresh=self.min_score_thresh,
            max_boxes_to_draw=self.max_boxes_to_draw
        )
        return prediction

    def predict(self, image: PImage) -> Prediction:
        tensor = self.preprocess(image)

        self.tflite_interpreter.set_tensor(
            self.input_details[0]['index'], tensor
        )
        self.tflite_interpreter.invoke()

        box_data = tf.convert_to_tensor(self.tflite_interpreter.get_tensor(
            self.output_details[0]['index']))
        class_data = tf.convert_to_tensor(self.tflite_interpreter.get_tensor(
            self.output_details[1]['index']))
        score_data = tf.convert_to_tensor(self.tflite_interpreter.get_tensor(
            self.output_details[2]['index']))
        num_detections = tf.convert_to_tensor(self.tflite_interpreter.get_tensor(
            self.output_details[3]['index']))

        class_data = tf.squeeze(
            class_data, axis=[0]).numpy().astype(np.int64) + 1
        box_data = tf.squeeze(box_data, axis=[0]).numpy()
        score_data = tf.squeeze(score_data, axis=[0]).numpy()
        num_detections = tf.squeeze(num_detections, axis=[0]).numpy()

        return Prediction(
            detection_boxes=box_data,
            detection_classes=class_data,
            detection_scores=score_data,
            num_detections=num_detections
        )

        

   