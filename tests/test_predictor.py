import pytest
import os
from PIL import Image as PImage
import numpy as np

from octoprint_nanny.predictor import (
    ThreadLocalPredictor,
    Prediction,
    predict_threadsafe,
)


@pytest.mark.syncio
async def test_zero_results(mock_response):

    (oh, ow), (vb, vh, vw), prediction = await predict_threadsafe(predict_bytes)


def test_area_of_intersection_overlap():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([[0.3, 0.3, 0.9, 0.9]])

    calibration_box = [0.2, 0.2, 0.8, 0.8]

    detection_scores = np.array([1])

    detection_classes = np.array([4])
    prediction = Prediction(
        detection_boxes=detection_boxes,
        detection_scores=detection_scores,
        detection_classes=detection_classes,
        num_detections=len(detection_boxes),
    )

    percent_area = predictor.percent_intersection(prediction, calibration_box)
    expected = (0.5 ** 2) / (0.6 ** 2)
    np.testing.assert_almost_equal(percent_area[0], expected)


def test_area_of_intersection_no_overlap_0():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([[0.3, 0.3, 0.9, 0.9]])

    calibration_box = [0.1, 0.1, 0.2, 0.2]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    prediction = Prediction(
        detection_boxes=detection_boxes,
        detection_scores=detection_scores,
        detection_classes=detection_classes,
        num_detections=len(detection_classes),
    )

    percent_area = predictor.percent_intersection(prediction, calibration_box)
    expected = 0.0
    np.testing.assert_almost_equal(percent_area[0], expected)


def test_area_of_intersection_no_overlap_1():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([[0.5, 0.2, 0.9, 0.4]])

    calibration_box = [0.1, 0.7, 0.39, 0.8]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    prediction = Prediction(
        detection_boxes=detection_boxes,
        detection_classes=detection_classes,
        detection_scores=detection_scores,
        num_detections=len(detection_classes),
    )

    percent_area = predictor.percent_intersection(prediction, calibration_box)
    expected = 0.0
    np.testing.assert_almost_equal(percent_area[0], expected)


def test_area_of_intersection_prediction_contained_0():

    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([[0.2, 0.2, 0.8, 0.8]])

    calibration_box = [0.1, 0.1, 0.9, 0.9]

    detection_scores = np.array([1])

    detection_classes = np.array([4])

    prediction = Prediction(
        detection_boxes=detection_boxes,
        detection_classes=detection_classes,
        detection_scores=detection_scores,
        num_detections=len(detection_classes),
    )

    percent_area = predictor.percent_intersection(prediction, calibration_box)
    expected = 1.0
    np.testing.assert_almost_equal(percent_area[0], expected)
