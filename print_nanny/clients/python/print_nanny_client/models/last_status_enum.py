# coding: utf-8

"""

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.0
    Generated by: https://openapi-generator.tech
"""


import pprint  # noqa: F401
import re  # noqa: F401

import six  # noqa: F401

from print_nanny_client.exceptions import ApiValueError  # noqa: F401
from print_nanny_client.model_utils import (  # noqa: F401
    ModelNormal,
    ModelSimple,
    check_allowed_values,
    check_validations
)


class LastStatusEnum(ModelSimple):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.

    Attributes:
      allowed_values (dict): The key is the tuple path to the attribute
          and the for var_name this is (var_name,). The value is a dict
          with a capitalized key describing the allowed value and an allowed
          value. These dicts store the allowed enum values.
      openapi_types (dict): The key is attribute name
          and the value is attribute type.
      validations (dict): The key is the tuple path to the attribute
          and the for var_name this is (var_name,). The value is a dict
          that stores validations for max_length, min_length, max_items,
          min_items, exclusive_maximum, inclusive_maximum, exclusive_minimum,
          inclusive_minimum, and regex.
    """

    allowed_values = {
        ('value',): {
            'STARTED': "STARTED",
            'DONE': "DONE",
            'FAILED': "FAILED",
            'CANCELLING': "CANCELLING",
            'CANCELLED': "CANCELLED",
            'PAUSED': "PAUSED",
            'RESUMED': "RESUMED"
        },
    }

    openapi_types = {
        'value': 'str'
    }

    validations = {
    }

    def __init__(self, value=None):  # noqa: E501
        """LastStatusEnum - a model defined in OpenAPI"""  # noqa: E501

        self._value = None
        self.discriminator = None

        self.value = value

    @property
    def value(self):
        """Gets the value of this LastStatusEnum.  # noqa: E501


        :return: The value of this LastStatusEnum.  # noqa: E501
        :rtype: str
        """
        return self._value

    @value.setter
    def value(self, value):  # noqa: E501
        """Sets the value of this LastStatusEnum.


        :param value: The value of this LastStatusEnum.  # noqa: E501
        :type: str
        """
        if value is None:
            raise ApiValueError("Invalid value for `value`, must not be `None`")  # noqa: E501
        check_allowed_values(
            self.allowed_values,
            ('value',),
            value,
            self.validations
        )

        self._value = (
            value
        )

    def to_str(self):
        """Returns the string representation of the model"""
        return str(self._value)

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, LastStatusEnum):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
