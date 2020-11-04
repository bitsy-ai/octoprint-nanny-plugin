
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

@pytest.fixture
def predictor():
    return ThreadLocalPredictor()

@pytest.mark.parametrize("infile,outfile", TEST_PARAMS)
def test_predict_and_write(infile, outfile, predictor, ):
    image = predictor.load_image(infile)
    prediction = predictor.predict(image)

    assert prediction['num_detections'] > 5
    prediction = predictor.postprocess(image, prediction)
    predictor.write_image(outfile, prediction['viz'])

