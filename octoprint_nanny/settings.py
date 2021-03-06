import asyncio
from datetime import datetime
import logging
import pytz

from octoprint_nanny.workers.monitoring import (
    MonitoringWorker,
)

import beeline

from print_nanny_client.models.octo_print_event_event_type_enum import (
    OctoPrintEventEventTypeEnum,
)

import octoprint_nanny.types
from octoprint_nanny.clients.mqtt import MQTTClient
from octoprint_nanny.clients.rest import RestAPIClient, API_CLIENT_EXCEPTIONS
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.types import (
    MonitoringModes,
    TrackedOctoPrintEvents,
    RemoteCommands,
)

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.settings")


class PluginSettingsMemoize:
    """
    Convenience methods/properties for accessing OctoPrint plugin settings and computed metadata
    """

    def __init__(self, plugin, mqtt_receive_queue):
        self.plugin = plugin
        self.mqtt_receive_queue = mqtt_receive_queue
        # stateful clients and computed settings that require re-initialization when settings change
        self._mqtt_client = None
        self._telemetry_events = None
        self._device_info = None
        self._rest_client = None
        self._calibration = None
        self._metadata = None
        self.environment = {}

    @beeline.traced("PluginSettingsMemoize.reset_device_settings_state")
    def reset_device_settings_state(self):
        self._mqtt_client = None
        self._device_info = None
        self._calibration = None

    @beeline.traced("PluginSettingsMemoize.reset_rest_client_state")
    def reset_rest_client_state(self):
        self._rest_client = None

    @beeline.traced("PluginSettingsMemoize.get_device_metadata")
    def get_device_metadata(self):
        metadata = dict(
            created_dt=datetime.now(pytz.timezone("UTC")),
            environment=self.environment,
        )
        metadata.update(self.device_info)
        return metadata

    @beeline.traced("PluginSettingsMemoize.get_print_job_metadata")
    def get_print_job_metadata(self):
        return dict(
            printer_data=self.plugin._printer.get_current_data(),
            printer_profile_data=self.plugin._printer_profile_manager.get_current_or_default(),
            temperatures=self.plugin._printer.get_current_temperatures(),
        )

    @beeline.traced("PluginSettingsMemoize.on_environment_detected")
    def on_environment_detected(self, environment):
        self.environment = environment

    @property
    def device_cloudiot_name(self):
        return self.plugin.get_setting("device_cloudiot_name")

    @property
    def device_id(self):
        return self.plugin.get_setting("device_id")

    @property
    def monitoring_active(self):
        return self.plugin.get_setting("monitoring_active")

    @property
    def device_info(self):
        if self._device_info is None:
            self._device_info = self.plugin.get_device_info()
        return self._device_info

    @property
    def device_serial(self):
        return self.plugin.get_setting("device_serial")

    @property
    def device_cloudiot_id(self):
        return self.plugin.get_setting("device_cloudiot_id")

    @property
    def device_private_key(self):
        return self.plugin.get_setting("device_private_key")

    @property
    def device_public_key(self):
        return self.plugin.get_setting("device_public_key")

    @property
    def ca_cert(self):
        return self.plugin.get_setting("ca_cert")

    @property
    def api_url(self):
        return self.plugin.get_setting("api_url")

    @property
    def auth_token(self):
        return self.plugin.get_setting("auth_token")

    @property
    def min_score_thresh(self):
        return self.plugin.get_setting("min_score_thresh")

    @property
    def monitoring_mode(self):
        return MonitoringModes(self.plugin.get_setting("monitoring_mode"))

    @property
    def ws_url(self):
        return self.plugin.get_setting("ws_url")

    @property
    def snapshot_url(self):
        return self.plugin.get_setting("snapshot_url")

    @property
    def user_id(self):
        return self.plugin.get_setting("user_id")

    @property
    def webcam_upload(self):
        return self.plugin.get_setting("webcam_upload")

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = octoprint_nanny.types.Metadata(
                user_id=self.user_id,
                device_id=self.device_id,
                device_cloudiot_id=self.device_cloudiot_id,
            )
        return self._metadata

    @property
    def calibration(self):
        if self._calibration is None:
            self._calibration = MonitoringWorker.calc_calibration(
                self.plugin.get_setting("calibrate_x0"),
                self.plugin.get_setting("calibrate_y0"),
                self.plugin.get_setting("calibrate_x1"),
                self.plugin.get_setting("calibrate_y1"),
            )
        return self._calibration

    @property
    def monitoring_frames_per_minute(self):
        return self.plugin.get_setting("monitoring_frames_per_minute")

    @property
    def rest_client(self):
        if self.auth_token is None:
            raise PluginSettingsRequired(f"auth_token is not set")
        if self._rest_client is None:
            self._rest_client = RestAPIClient(
                auth_token=self.auth_token, api_url=self.api_url
            )
            logger.info(f"RestAPIClient initialized with api_url={self.api_url}")
        return self._rest_client

    def test_mqtt_settings(self):
        if (
            self.device_cloudiot_id is None
            or self.device_private_key is None
            or self.ca_cert is None
        ):
            raise PluginSettingsRequired(
                f"Received None for device_cloudiot_id={self.device_cloudiot_id} or private_key_file={self.device_private_key} or ca_cert={self.ca_cert}"
            )
        return True

    @property
    def mqtt_client(self):
        self.test_mqtt_settings()
        if self._mqtt_client is None:
            self._mqtt_client = MQTTClient(
                device_id=self.device_id,
                device_cloudiot_id=self.device_cloudiot_id,
                private_key_file=self.device_private_key,
                ca_cert=self.ca_cert,
                mqtt_receive_queue=self.mqtt_receive_queue,
                trace_context=self.get_device_metadata(),
            )
        return self._mqtt_client

    def event_is_tracked(self, event_type):
        return TrackedOctoPrintEvents.is_member(event_type) or RemoteCommands.is_member(
            event_type
        )
