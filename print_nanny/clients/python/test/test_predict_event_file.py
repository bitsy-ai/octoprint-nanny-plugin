# coding: utf-8

"""

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.0
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest
import datetime

import print_nanny_client
from print_nanny_client.models.predict_event_file import PredictEventFile  # noqa: E501
from print_nanny_client.rest import ApiException


class TestPredictEventFile(unittest.TestCase):
    """PredictEventFile unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test PredictEventFile
        include_option is a boolean, when False only required
        params are included, when True both required and
        optional params are included"""
        # model = print_nanny_client.models.predict_event_file.PredictEventFile()  # noqa: E501
        if include_optional:
            return PredictEventFile(
                id=56, annotated_image="", hash="", original_image="", url=""
            )
        else:
            return PredictEventFile(
                annotated_image="",
                hash="",
                original_image="",
            )

    def testPredictEventFile(self):
        """Test PredictEventFile"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == "__main__":
    unittest.main()