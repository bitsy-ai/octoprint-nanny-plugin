# coding: utf-8

"""

    No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)  # noqa: E501

    OpenAPI spec version: 0.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class OctoPrintEventRequest(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'dt': 'datetime',
        'event_type': 'str',
        'event_data': 'dict(str, Object)',
        'plugin_version': 'str',
        'octoprint_version': 'str'
    }

    attribute_map = {
        'dt': 'dt',
        'event_type': 'event_type',
        'event_data': 'event_data',
        'plugin_version': 'plugin_version',
        'octoprint_version': 'octoprint_version'
    }

    def __init__(self, dt=None, event_type=None, event_data=None, plugin_version=None, octoprint_version=None):  # noqa: E501
        """OctoPrintEventRequest - a model defined in Swagger"""  # noqa: E501
        self._dt = None
        self._event_type = None
        self._event_data = None
        self._plugin_version = None
        self._octoprint_version = None
        self.discriminator = None
        self.dt = dt
        self.event_type = event_type
        self.event_data = event_data
        self.plugin_version = plugin_version
        self.octoprint_version = octoprint_version

    @property
    def dt(self):
        """Gets the dt of this OctoPrintEventRequest.  # noqa: E501


        :return: The dt of this OctoPrintEventRequest.  # noqa: E501
        :rtype: datetime
        """
        return self._dt

    @dt.setter
    def dt(self, dt):
        """Sets the dt of this OctoPrintEventRequest.


        :param dt: The dt of this OctoPrintEventRequest.  # noqa: E501
        :type: datetime
        """
        if dt is None:
            raise ValueError("Invalid value for `dt`, must not be `None`")  # noqa: E501

        self._dt = dt

    @property
    def event_type(self):
        """Gets the event_type of this OctoPrintEventRequest.  # noqa: E501


        :return: The event_type of this OctoPrintEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._event_type

    @event_type.setter
    def event_type(self, event_type):
        """Sets the event_type of this OctoPrintEventRequest.


        :param event_type: The event_type of this OctoPrintEventRequest.  # noqa: E501
        :type: str
        """
        if event_type is None:
            raise ValueError("Invalid value for `event_type`, must not be `None`")  # noqa: E501

        self._event_type = event_type

    @property
    def event_data(self):
        """Gets the event_data of this OctoPrintEventRequest.  # noqa: E501


        :return: The event_data of this OctoPrintEventRequest.  # noqa: E501
        :rtype: dict(str, Object)
        """
        return self._event_data

    @event_data.setter
    def event_data(self, event_data):
        """Sets the event_data of this OctoPrintEventRequest.


        :param event_data: The event_data of this OctoPrintEventRequest.  # noqa: E501
        :type: dict(str, Object)
        """
        if event_data is None:
            raise ValueError("Invalid value for `event_data`, must not be `None`")  # noqa: E501

        self._event_data = event_data

    @property
    def plugin_version(self):
        """Gets the plugin_version of this OctoPrintEventRequest.  # noqa: E501


        :return: The plugin_version of this OctoPrintEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._plugin_version

    @plugin_version.setter
    def plugin_version(self, plugin_version):
        """Sets the plugin_version of this OctoPrintEventRequest.


        :param plugin_version: The plugin_version of this OctoPrintEventRequest.  # noqa: E501
        :type: str
        """
        if plugin_version is None:
            raise ValueError("Invalid value for `plugin_version`, must not be `None`")  # noqa: E501

        self._plugin_version = plugin_version

    @property
    def octoprint_version(self):
        """Gets the octoprint_version of this OctoPrintEventRequest.  # noqa: E501


        :return: The octoprint_version of this OctoPrintEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._octoprint_version

    @octoprint_version.setter
    def octoprint_version(self, octoprint_version):
        """Sets the octoprint_version of this OctoPrintEventRequest.


        :param octoprint_version: The octoprint_version of this OctoPrintEventRequest.  # noqa: E501
        :type: str
        """
        if octoprint_version is None:
            raise ValueError("Invalid value for `octoprint_version`, must not be `None`")  # noqa: E501

        self._octoprint_version = octoprint_version

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(OctoPrintEventRequest, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, OctoPrintEventRequest):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
