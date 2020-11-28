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
from print_nanny_client.models.paginated_octo_print_event_list import (
    PaginatedOctoPrintEventList,
)  # noqa: E501
from print_nanny_client.rest import ApiException


class TestPaginatedOctoPrintEventList(unittest.TestCase):
    """PaginatedOctoPrintEventList unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test PaginatedOctoPrintEventList
        include_option is a boolean, when False only required
        params are included, when True both required and
        optional params are included"""
        # model = print_nanny_client.models.paginated_octo_print_event_list.PaginatedOctoPrintEventList()  # noqa: E501
        if include_optional:
            return PaginatedOctoPrintEventList(
                count=123,
                next="http://api.example.org/accounts/?offset=400&limit=100",
                previous="http://api.example.org/accounts/?offset=200&limit=100",
                results=[
                    print_nanny_client.models.octo_print_event.OctoPrintEvent(
                        id=56,
                        dt=datetime.datetime.strptime(
                            "2013-10-20 19:20:30.00", "%Y-%m-%d %H:%M:%S.%f"
                        ),
                        event_type="ClientAuthed",
                        event_data={"key": null},
                        user=56,
                        plugin_version="",
                        octoprint_version="",
                        print_job=56,
                        url="",
                    )
                ],
            )
        else:
            return PaginatedOctoPrintEventList()

    def testPaginatedOctoPrintEventList(self):
        """Test PaginatedOctoPrintEventList"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == "__main__":
    unittest.main()
