
import pytest
import os
from PIL import Image as PImage
import numpy as np

from print_nanny.predictor import ThreadLocalPredictor, Prediction

TEST_INPUT = [
    'data/images/1.pre.jpg'
]
TEST_OUTPUT = [
    'data/images/1.post.jpg'
]




@pytest.fixture
def predictor():
    return ThreadLocalPredictor()

@pytest.fixture
def image(predictor):
    return predictor.load_image(TEST_INPUT[0])

@pytest.fixture
def prediction(image, predictor):
    return predictor.predict(image)

TEST_PARAMS = [
    (
        f'data/images/{i}.pre.jpg',
        f'data/images/{i}.post.jpg'
    ) for i in range(0,7)
]

@pytest.mark.parametrize("infile,outfile", TEST_PARAMS)
def test_predict_and_draw(infile, outfile, predictor, ):
    image = predictor.load_image(infile)
    prediction = predictor.predict(image)

    assert prediction['num_detections'] > 5
    img = PImage.fromarray(predictor.postprocess(image, prediction))
    print(f'Saving outfile {outfile}')

    img.save(outfile)

