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
from print_nanny_client.models.patched_printer_profile_request import PatchedPrinterProfileRequest  # noqa: E501
from print_nanny_client.rest import ApiException

class TestPatchedPrinterProfileRequest(unittest.TestCase):
    """PatchedPrinterProfileRequest unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test PatchedPrinterProfileRequest
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = print_nanny_client.models.patched_printer_profile_request.PatchedPrinterProfileRequest()  # noqa: E501
        if include_optional :
            return PatchedPrinterProfileRequest(
                axes_e_inverted = True, 
                axes_e_speed = -2147483648, 
                axes_x_speed = -2147483648, 
                axes_y_inverted = True, 
                axes_y_speed = -2147483648, 
                axes_z_inverted = True, 
                axes_z_speed = -2147483648, 
                extruder_count = -2147483648, 
                extruder_nozzle_diameter = 1.337, 
                extruder_offsets = [
                    1.337
                    ], 
                extruder_shared_nozzle = True, 
                heated_bed = True, 
                heated_chamber = True, 
                model = '0', 
                name = '0', 
                volume_custom_box = True, 
                volume_depth = 1.337, 
                volume_form_factor = '0', 
                volume_height = 1.337, 
                volume_origin = '0'
            )
        else :
            return PatchedPrinterProfileRequest(
        )

    def testPatchedPrinterProfileRequest(self):
        """Test PatchedPrinterProfileRequest"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
