# coding: utf-8

"""

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.0
    Generated by: https://openapi-generator.tech
"""


import inspect
import pprint
import re  # noqa: F401
import six

from print_nanny_client.configuration import Configuration


class GcodeFileRequest(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {"name": "str", "file": "file", "file_hash": "str"}

    attribute_map = {"name": "name", "file": "file", "file_hash": "file_hash"}

    def __init__(
        self, name=None, file=None, file_hash=None, local_vars_configuration=None
    ):  # noqa: E501
        """GcodeFileRequest - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._name = None
        self._file = None
        self._file_hash = None
        self.discriminator = None

        self.name = name
        self.file = file
        self.file_hash = file_hash

    @property
    def name(self):
        """Gets the name of this GcodeFileRequest.  # noqa: E501


        :return: The name of this GcodeFileRequest.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this GcodeFileRequest.


        :param name: The name of this GcodeFileRequest.  # noqa: E501
        :type name: str
        """
        if (
            self.local_vars_configuration.client_side_validation and name is None
        ):  # noqa: E501
            raise ValueError(
                "Invalid value for `name`, must not be `None`"
            )  # noqa: E501
        if (
            self.local_vars_configuration.client_side_validation
            and name is not None
            and len(name) > 255
        ):
            raise ValueError(
                "Invalid value for `name`, length must be less than or equal to `255`"
            )  # noqa: E501

        self._name = name

    @property
    def file(self):
        """Gets the file of this GcodeFileRequest.  # noqa: E501


        :return: The file of this GcodeFileRequest.  # noqa: E501
        :rtype: file
        """
        return self._file

    @file.setter
    def file(self, file):
        """Sets the file of this GcodeFileRequest.


        :param file: The file of this GcodeFileRequest.  # noqa: E501
        :type file: file
        """
        if (
            self.local_vars_configuration.client_side_validation and file is None
        ):  # noqa: E501
            raise ValueError(
                "Invalid value for `file`, must not be `None`"
            )  # noqa: E501

        self._file = file

    @property
    def file_hash(self):
        """Gets the file_hash of this GcodeFileRequest.  # noqa: E501


        :return: The file_hash of this GcodeFileRequest.  # noqa: E501
        :rtype: str
        """
        return self._file_hash

    @file_hash.setter
    def file_hash(self, file_hash):
        """Sets the file_hash of this GcodeFileRequest.


        :param file_hash: The file_hash of this GcodeFileRequest.  # noqa: E501
        :type file_hash: str
        """
        if (
            self.local_vars_configuration.client_side_validation and file_hash is None
        ):  # noqa: E501
            raise ValueError(
                "Invalid value for `file_hash`, must not be `None`"
            )  # noqa: E501
        if (
            self.local_vars_configuration.client_side_validation
            and file_hash is not None
            and len(file_hash) > 255
        ):
            raise ValueError(
                "Invalid value for `file_hash`, length must be less than or equal to `255`"
            )  # noqa: E501

        self._file_hash = file_hash

    def to_dict(self, serialize=False):
        """Returns the model properties as a dict"""
        result = {}

        def convert(x):
            if hasattr(x, "to_dict"):
                args = inspect.getargspec(x.to_dict).args
                if len(args) == 1:
                    return x.to_dict()
                else:
                    return x.to_dict(serialize)
            else:
                return x

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            attr = self.attribute_map.get(attr, attr) if serialize else attr
            if isinstance(value, list):
                result[attr] = list(map(lambda x: convert(x), value))
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(lambda item: (item[0], convert(item[1])), value.items())
                )
            else:
                result[attr] = convert(value)

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, GcodeFileRequest):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, GcodeFileRequest):
            return True

        return self.to_dict() != other.to_dict()
