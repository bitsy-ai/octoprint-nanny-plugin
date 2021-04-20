import pytest
import logging
import os
from PIL import Image as PImage
import numpy as np
from octoprint_nanny.types import BoundingBoxPrediction
from octoprint_nanny.predictor import (
    ThreadLocalPredictor,
    predict_threadsafe,
    print_is_healthy,
    explode_prediction_df,
)

logger = logging.getLogger(__name__)
try:
    import pandas as pd
except:
    logger.warning("Offline dependencies not found")


def test_area_of_intersection_overlap():
    predictor = ThreadLocalPredictor()
    detection_boxes = np.array([[0.3, 0.3, 0.9, 0.9]])

    calibration_box = [0.2, 0.2, 0.8, 0.8]

    detection_scores = np.array([1])

    detection_classes = np.array([4])
    prediction = BoundingBoxPrediction(
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

    prediction = BoundingBoxPrediction(
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

    prediction = BoundingBoxPrediction(
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

    prediction = BoundingBoxPrediction(
        detection_boxes=detection_boxes,
        detection_classes=detection_classes,
        detection_scores=detection_scores,
        num_detections=len(detection_classes),
    )

    percent_area = predictor.percent_intersection(prediction, calibration_box)
    expected = 1.0
    np.testing.assert_almost_equal(percent_area[0], expected)


def test_print_health_trend_increasing():
    num_detections = 40
    prediction1 = BoundingBoxPrediction(
        detection_classes=np.repeat(4, num_detections),
        detection_scores=np.linspace(0, 0.6, num=num_detections),
        num_detections=num_detections,
        detection_boxes=np.repeat([0.1, 0.1, 0.8, 0.8], num_detections),
    )
    prediction2 = BoundingBoxPrediction(
        detection_classes=np.repeat(4, num_detections),
        detection_scores=np.linspace(0.7, 1, num=num_detections),
        num_detections=num_detections,
        detection_boxes=np.repeat([0.1, 0.1, 0.8, 0.8], num_detections),
    )
    df = explode_prediction_df(1234, prediction1)
    df = df.append(explode_prediction_df(2345, prediction2))

    assert print_is_healthy(df) == True


def test_print_health_trend_decreasing():
    num_detections = 40
    classes = np.concatenate(
        [
            np.repeat(4, num_detections // 2),  # print
            np.repeat(3, num_detections // 2),  # spaghetti
        ]
    )

    scores1 = np.concatenate(
        [
            np.linspace(0, 0.6, num=num_detections // 2),  # print
            np.linspace(0.4, 0.8, num=num_detections // 2),  # spaghetti
        ]
    )

    scores2 = np.concatenate(
        [
            np.linspace(0, 0.7, num=num_detections // 2),  # print
            np.linspace(0.6, 0.9, num=num_detections // 2),  # spaghetti
        ]
    )

    prediction1 = BoundingBoxPrediction(
        detection_classes=classes,
        detection_scores=scores1,
        num_detections=num_detections,
        detection_boxes=np.repeat([0.1, 0.1, 0.8, 0.8], num_detections),
    )
    prediction2 = BoundingBoxPrediction(
        detection_classes=classes,
        detection_scores=scores2,
        num_detections=num_detections,
        detection_boxes=np.repeat([0.1, 0.1, 0.8, 0.8], num_detections),
    )
    df = explode_prediction_df(1234, prediction1)
    df = df.append(explode_prediction_df(2345, prediction2))

    assert print_is_healthy(df) == False


def test_print_health_trend_initial():
    num_detections = 40
    prediction = BoundingBoxPrediction(
        detection_classes=np.repeat(4, num_detections),
        detection_scores=np.linspace(0, 1, num=num_detections),
        num_detections=num_detections,
        detection_boxes=np.repeat([0.1, 0.1, 0.8, 0.8], num_detections),
    )
    df = explode_prediction_df(1234, prediction)

    assert print_is_healthy(df) == True
