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


class PredictEventRequest(object):
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
    openapi_types = {
        'dt': 'datetime',
        'original_image': 'file',
        'annotated_image': 'file',
        'event_data': 'str',
        'plugin_version': 'str',
        'octoprint_version': 'str',
        'print_job': 'int'
    }

    attribute_map = {
        'dt': 'dt',
        'original_image': 'original_image',
        'annotated_image': 'annotated_image',
        'event_data': 'event_data',
        'plugin_version': 'plugin_version',
        'octoprint_version': 'octoprint_version',
        'print_job': 'print_job'
    }

    def __init__(self, dt=None, original_image=None, annotated_image=None, event_data=None, plugin_version=None, octoprint_version=None, print_job=None, local_vars_configuration=None):  # noqa: E501
        """PredictEventRequest - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._dt = None
        self._original_image = None
        self._annotated_image = None
        self._event_data = None
        self._plugin_version = None
        self._octoprint_version = None
        self._print_job = None
        self.discriminator = None

        self.dt = dt
        self.original_image = original_image
        self.annotated_image = annotated_image
        self.event_data = event_data
        self.plugin_version = plugin_version
        self.octoprint_version = octoprint_version
        self.print_job = print_job

    @property
    def dt(self):
        """Gets the dt of this PredictEventRequest.  # noqa: E501


        :return: The dt of this PredictEventRequest.  # noqa: E501
        :rtype: datetime
        """
        return self._dt

    @dt.setter
    def dt(self, dt):
        """Sets the dt of this PredictEventRequest.


        :param dt: The dt of this PredictEventRequest.  # noqa: E501
        :type dt: datetime
        """
        if self.local_vars_configuration.client_side_validation and dt is None:  # noqa: E501
            raise ValueError("Invalid value for `dt`, must not be `None`")  # noqa: E501

        self._dt = dt

    @property
    def original_image(self):
        """Gets the original_image of this PredictEventRequest.  # noqa: E501


        :return: The original_image of this PredictEventRequest.  # noqa: E501
        :rtype: file
        """
        return self._original_image

    @original_image.setter
    def original_image(self, original_image):
        """Sets the original_image of this PredictEventRequest.


        :param original_image: The original_image of this PredictEventRequest.  # noqa: E501
        :type original_image: file
        """
        if self.local_vars_configuration.client_side_validation and original_image is None:  # noqa: E501
            raise ValueError("Invalid value for `original_image`, must not be `None`")  # noqa: E501

        self._original_image = original_image

    @property
    def annotated_image(self):
        """Gets the annotated_image of this PredictEventRequest.  # noqa: E501


        :return: The annotated_image of this PredictEventRequest.  # noqa: E501
        :rtype: file
        """
        return self._annotated_image

    @annotated_image.setter
    def annotated_image(self, annotated_image):
        """Sets the annotated_image of this PredictEventRequest.


        :param annotated_image: The annotated_image of this PredictEventRequest.  # noqa: E501
        :type annotated_image: file
        """
        if self.local_vars_configuration.client_side_validation and annotated_image is None:  # noqa: E501
            raise ValueError("Invalid value for `annotated_image`, must not be `None`")  # noqa: E501

        self._annotated_image = annotated_image

    @property
    def event_data(self):
        """Gets the event_data of this PredictEventRequest.  # noqa: E501


        :return: The event_data of this PredictEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._event_data

    @event_data.setter
    def event_data(self, event_data):
        """Sets the event_data of this PredictEventRequest.


        :param event_data: The event_data of this PredictEventRequest.  # noqa: E501
        :type event_data: str
        """
        if self.local_vars_configuration.client_side_validation and event_data is None:  # noqa: E501
            raise ValueError("Invalid value for `event_data`, must not be `None`")  # noqa: E501

        self._event_data = event_data

    @property
    def plugin_version(self):
        """Gets the plugin_version of this PredictEventRequest.  # noqa: E501


        :return: The plugin_version of this PredictEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._plugin_version

    @plugin_version.setter
    def plugin_version(self, plugin_version):
        """Sets the plugin_version of this PredictEventRequest.


        :param plugin_version: The plugin_version of this PredictEventRequest.  # noqa: E501
        :type plugin_version: str
        """
        if self.local_vars_configuration.client_side_validation and plugin_version is None:  # noqa: E501
            raise ValueError("Invalid value for `plugin_version`, must not be `None`")  # noqa: E501
        if (self.local_vars_configuration.client_side_validation and
                plugin_version is not None and len(plugin_version) > 30):
            raise ValueError("Invalid value for `plugin_version`, length must be less than or equal to `30`")  # noqa: E501

        self._plugin_version = plugin_version

    @property
    def octoprint_version(self):
        """Gets the octoprint_version of this PredictEventRequest.  # noqa: E501


        :return: The octoprint_version of this PredictEventRequest.  # noqa: E501
        :rtype: str
        """
        return self._octoprint_version

    @octoprint_version.setter
    def octoprint_version(self, octoprint_version):
        """Sets the octoprint_version of this PredictEventRequest.


        :param octoprint_version: The octoprint_version of this PredictEventRequest.  # noqa: E501
        :type octoprint_version: str
        """
        if self.local_vars_configuration.client_side_validation and octoprint_version is None:  # noqa: E501
            raise ValueError("Invalid value for `octoprint_version`, must not be `None`")  # noqa: E501
        if (self.local_vars_configuration.client_side_validation and
                octoprint_version is not None and len(octoprint_version) > 30):
            raise ValueError("Invalid value for `octoprint_version`, length must be less than or equal to `30`")  # noqa: E501

        self._octoprint_version = octoprint_version

    @property
    def print_job(self):
        """Gets the print_job of this PredictEventRequest.  # noqa: E501


        :return: The print_job of this PredictEventRequest.  # noqa: E501
        :rtype: int
        """
        return self._print_job

    @print_job.setter
    def print_job(self, print_job):
        """Sets the print_job of this PredictEventRequest.


        :param print_job: The print_job of this PredictEventRequest.  # noqa: E501
        :type print_job: int
        """

        self._print_job = print_job

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
                result[attr] = list(map(
                    lambda x: convert(x),
                    value
                ))
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], convert(item[1])),
                    value.items()
                ))
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
        if not isinstance(other, PredictEventRequest):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, PredictEventRequest):
            return True

        return self.to_dict() != other.to_dict()
