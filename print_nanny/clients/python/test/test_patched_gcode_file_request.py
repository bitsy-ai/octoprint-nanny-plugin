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
from print_nanny_client.models.patched_gcode_file_request import (
    PatchedGcodeFileRequest,
)  # noqa: E501
from print_nanny_client.rest import ApiException


class TestPatchedGcodeFileRequest(unittest.TestCase):
    """PatchedGcodeFileRequest unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test PatchedGcodeFileRequest
        include_option is a boolean, when False only required
        params are included, when True both required and
        optional params are included"""
        # model = print_nanny_client.models.patched_gcode_file_request.PatchedGcodeFileRequest()  # noqa: E501
        if include_optional:
            return PatchedGcodeFileRequest(name="", file=bytes(b"blah"), file_hash="")
        else:
            return PatchedGcodeFileRequest()

    def testPatchedGcodeFileRequest(self):
        """Test PatchedGcodeFileRequest"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == "__main__":
    unittest.main()
