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
from print_nanny_client.models.paginated_gcode_file_list import PaginatedGcodeFileList  # noqa: E501
from print_nanny_client.rest import ApiException

class TestPaginatedGcodeFileList(unittest.TestCase):
    """PaginatedGcodeFileList unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test PaginatedGcodeFileList
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = print_nanny_client.models.paginated_gcode_file_list.PaginatedGcodeFileList()  # noqa: E501
        if include_optional :
            return PaginatedGcodeFileList(
                count = 123, 
                next = 'http://api.example.org/accounts/?offset=400&limit=100', 
                previous = 'http://api.example.org/accounts/?offset=200&limit=100', 
                results = [
                    print_nanny_client.models.gcode_file.GcodeFile(
                        id = 56, 
                        user = 56, 
                        name = '', 
                        file = '', 
                        file_hash = '', 
                        url = '', )
                    ]
            )
        else :
            return PaginatedGcodeFileList(
        )

    def testPaginatedGcodeFileList(self):
        """Test PaginatedGcodeFileList"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
