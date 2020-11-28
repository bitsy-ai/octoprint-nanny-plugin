
import pytest
import os
from PIL import Image as PImage
import numpy as np

from print_nanny.predictor import ThreadLocalPredictor, Prediction

TEST_PARAMS = [
    (
        f'data/images/{i}.pre.jpg',
        f'data/images/{i}.post.jpg'
    ) for i in range(0,7)
]

def test_area_of_intersection_overlap():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([
        [0.3, 0.3, 0.9, 0.9]
    ])

    calibration_box = [0.2, 0.2, 0.8, 0.8]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    percent_area = predictor.percent_intersection(detection_boxes, detection_scores, detection_classes, calibration_box)
    expected =  ((0.5**2) / (0.6**2))
    np.testing.assert_almost_equal(percent_area[0],expected)


def test_area_of_intersection_no_overlap_0():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([
        [0.3, 0.3, 0.9, 0.9]
    ])

    calibration_box = [0.1, 0.1, 0.2, 0.2]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    percent_area = predictor.percent_intersection(detection_boxes, detection_scores, detection_classes, calibration_box)
    expected = 0.0
    np.testing.assert_almost_equal(percent_area[0],expected)

def test_area_of_intersection_no_overlap_1():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([
        [0.5, 0.2, 0.9, 0.4]
    ])

    calibration_box = [0.1, 0.7, 0.39, 0.8]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    percent_area = predictor.percent_intersection(detection_boxes, detection_scores, detection_classes, calibration_box)
    expected = 0.0
    np.testing.assert_almost_equal(percent_area[0],expected)

def test_area_of_intersection_prediction_contained_0():

    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([
        [0.2, 0.2, 0.8, 0.8]
    ])

    calibration_box = [0.1, 0.1, 0.9, 0.9]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    percent_area = predictor.percent_intersection(detection_boxes, detection_scores, detection_classes, calibration_box)
    expected = 1.0
    np.testing.assert_almost_equal(percent_area[0],expected)
