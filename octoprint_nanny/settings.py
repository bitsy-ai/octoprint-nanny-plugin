from datetime import datetime
import logging
import pytz
import numpy as np
import octoprint
import beeline
import uuid

from print_nanny_client import (
    PrintNannyPluginEventEventTypeEnum as PrintNannyPluginEventType,
    OctoPrintEventEventTypeEnum as OctoPrintEventType,
    PrintJobStatusEnum,
    RemoteCommandEventEventTypeEnum as RemoteCommandEventType,
)

from octoprint_nanny.clients.mqtt import MQTTClient
from octoprint_nanny.clients.rest import RestAPIClient
from octoprint_nanny.exceptions import PluginSettingsRequired
from octoprint_nanny.types import (
    MonitoringModes,
    Metadata,
)
import print_nanny_client

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.settings")


class PluginSettingsMemoize:
    """
    Convenience methods/properties for accessing:
        1. OctoPrint plugin settings
        2. Data pre-serialized to REST & Protobuf representation

    REST serialization supports HTTP1 REST API (OpenAPI 3.0 schema)
    Protobuf serialization supports MQTT & data structures used in apache beam pipelines
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

        self._print_session_rest = None
        self._print_session_pb = None
        self._octoprint_environment = None

    def reset_print_session(self):
        self._print_session_rest = None
        self._print_session_pb = None

    @beeline.traced("PluginSettingsMemoize.reset_device_settings_state")
    def reset_device_settings_state(self):
        self._mqtt_client = None
        self._device_info = None
        self._calibration = None

    @beeline.traced("PluginSettingsMemoize.reset_rest_client_state")
    def reset_rest_client_state(self):
        self._rest_client = None

    @beeline.traced("PluginSettingsMemoize.get_current_octoprint_job")
    def get_current_octoprint_job(self):
        """
        GET /api/job HTTP/1.1
            {
            "job": {
                "file": {
                "name": "whistle_v2.gcode",
                "origin": "local",
                "size": 1468987,
                "date": 1378847754
                },
                "estimatedPrintTime": 8811,
                "filament": {
                "tool0": {
                    "length": 810,
                    "volume": 5.36
                }
                }
            },
            "progress": {
                "completion": 0.2298468264184775,
                "filepos": 337942,
                "printTime": 276,
                "printTimeLeft": 912
            },
            "state": "Printing"
            }
        """
        return self.plugin._printer.get_current_job()

    @beeline.traced("PluginSettingsMemoize.get_current_octoprint_profile")
    def get_current_octoprint_profile(self):
        """
        HTTP/1.1 200 OK
        Content-Type: application/json
        {
            "profile": {
                "id": "some_profile",
                "name": "Some profile",
                "color": "default",
                "model": "Some cool model",
                "default": false,
                "current": false,
                "resource": "http://example.com/api/printerprofiles/some_profile",
                "volume": {
                "formFactor": "rectangular",
                "origin": "lowerleft",
                "width": 200,
                "depth": 200,
                "height": 200
                },
                "heatedBed": true,
                "heatedChamber": false,
                "axes": {
                "x": {
                    "speed": 6000,
                    "inverted": false
                },
                "y": {
                    "speed": 6000,
                    "inverted": false
                },
                "z": {
                    "speed": 200,
                    "inverted": false
                },
                "e": {
                    "speed": 300,
                    "inverted": false
                }
                },
                "extruder": {
                "count": 1,
                "offsets": [
                    {"x": 0.0, "y": 0.0}
                ]
                }
            }
        }
        """
        return self.plugin._printer_profile_manager.get_current_or_default()

    def get_current_octoprint_temperatures(self):
        return self.plugin._printer.get_current_temperatures()

    def get_current_octoprint_printer_state(self):
        """
        {'state': {'text': 'Offline', 'flags': {'operational': False, 'printing': False, 'cancelling': False, 'pausing': False, 'resuming': False, 'finishing': False, 'closedOrError': True, 'error': False, 'paused': False, 'ready': False, 'sdReady': False}, 'error': ''}, 'job': {'file': {'name': None, 'path': None, 'size': None, 'origin': None, 'date': None}, 'estimatedPrintTime': None, 'lastPrintTime': None, 'filament': {'length': None, 'volume': None}, 'user': None}, 'currentZ': None, 'progress': {'completion': None, 'filepos': None, 'printTime': None, 'printTimeLeft': None, 'printTimeOrigin': None}, 'offsets': {}, 'resends': {'count': 0, 'ratio': 0}}
        """
        return self.plugin._printer.get_current_data()

    def on_environment_detected(self, environment):
        self._octoprint_environment = environment

    @property
    def data_folder(self):
        return self.plugin.get_plugin_data_folder()

    @property
    def logfile_path(self):
        return self.plugin._settings.get_plugin_logfile_path()

    @property
    def device_cloudiot_name(self):
        return self.plugin.get_setting("device_cloudiot_name")

    @property
    def octoprint_device_id(self):
        return self.plugin.get_setting("octoprint_device_id")

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
    def cloudiot_device_id(self):
        return self.plugin.get_setting("cloudiot_device_id")

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
    def auto_start(self):
        return self.plugin.get_setting("auto_start")

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
    def print_session_rest(self):
        return self._print_session_rest

    @property
    def print_session_pb(self):
        return self._print_session_pb

    async def create_print_session(self):
        session = uuid.uuid4().hex
        octoprint_job = self.get_current_octoprint_job()

        gcode_filename = None
        if octoprint_job.get("job") and octoprint_job.get("job").get("file"):
            gcode_filename = gcode_filename

        # @todo sync gcode file to remote

        printer_profile = self.get_current_octoprint_profile()
        printer_profile = await self.rest_client.update_or_create_printer_profile(
            printer_profile, self.octoprint_device_id
        )

        now = datetime.utcnow()

        print_session = await self.rest_client.create_print_session(
            gcode_filename=gcode_filename,
            session=session,
            printer_profile=printer_profile.id,
            octoprint_device=self.octoprint_device_id,
            octoprint_job=octoprint_job,
            created_dt=now,
        )
        self._print_session_rest = print_session
        self._print_session_pb = print_nanny_client.protobuf.common_pb2.PrintSession(
            session=session, id=print_session.id, created_ts=now.timestamp()
        )
        return self._print_session_rest

    @property
    def octoprint_environment(self):
        return self._octoprint_environment

    @property
    def metadata(self):
        ts = datetime.now(pytz.timezone("UTC")).timestamp()
        print_session = (
            self.print_session_rest.session if self.print_session_rest else None
        )
        print_session_id = (
            self.print_session_rest.id if self.print_session_rest else None
        )
        return Metadata(
            user_id=self.user_id,
            octoprint_device_id=self.octoprint_device_id,
            cloudiot_device_id=self.cloudiot_device_id,
            print_session=print_session,
            print_session_id=print_session_id,
            client_version=print_nanny_client.__version__,
            ts=ts,
            octoprint_environment=self.octoprint_environment,
            octoprint_version=octoprint.util.version.get_octoprint_version_string(),
            plugin_version=self.plugin._plugin_version,
        )

    @property
    def metadata_pb(self):
        ts = datetime.now(pytz.timezone("UTC")).timestamp()
        return print_nanny_client.protobuf.monitoring_pb2.Metadata(
            user_id=self.user_id,
            octoprint_device_id=self.octoprint_device_id,
            cloudiot_device_id=self.cloudiot_device_id,
            print_session=self.print_session_pb,
            ts=ts,
            octoprint_environment=self.octoprint_environment_pb,
        )

    @property
    def octoprint_environment_pb(self):
        octoprint_environment = self.octoprint_environment
        return print_nanny_client.protobuf.common_pb2.OctoprintEnvironment(
            plugin_version=self.plugin._plugin_version,
            client_version=print_nanny_client.__version__,
            python_version=octoprint_environment.get("python", {}).get("version"),
            pip_version=octoprint_environment.get("python", {}).get("pip"),
            octopi_version=octoprint_environment.get("plugins", {})
            .get("pi_support", {})
            .get("octopi_version"),
            virtualenv=octoprint_environment.get("python", {}).get("virtualenv"),
            platform=octoprint_environment.get("os", {}).get("platform"),
            bits=octoprint_environment.get("os", {}).get("bits"),
            cores=octoprint_environment.get("hardware", {}).get("cores"),
            freq=octoprint_environment.get("hardware", {}).get("freq"),
            ram=octoprint_environment.get("hardware", {}).get("ram"),
            pi_model=octoprint_environment.get("plugins", {})
            .get("pi_support", {})
            .get("model"),
            pi_throttle_state=octoprint_environment.get("plugins", {})
            .get("pi_support", {})
            .get("throttle_state"),
            octoprint_version=octoprint.util.version.get_octoprint_version_string(),
        )

    def calc_calibration(x0, y0, x1, y1, height=480, width=640):
        if (
            x0 is None
            or y0 is None
            or x1 is None
            or y1 is None
            or height is None
            or width is None
        ):
            logger.warning(f"Invalid calibration values ({x0}, {y0}) ({x1}, {y1})")
            return None

        mask = np.zeros((height, width))
        for (h, w), _ in np.ndenumerate(np.zeros((height, width))):
            value = (
                1 if (h / height >= y0 and h / height <= y1 and w / width >= x0) else 0
            )
            mask[h][w] = value

        mask = mask.astype(np.uint8)
        logger.info(f"Calibration set")

    @property
    def calibration(self):
        if self._calibration is None:
            self._calibration = self.calc_calibration(
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
            self.cloudiot_device_id is None
            or self.device_private_key is None
            or self.ca_cert is None
        ):
            raise PluginSettingsRequired(
                f"Received None for cloudiot_device_id={self.cloudiot_device_id} or private_key_file={self.device_private_key} or ca_cert={self.ca_cert}"
            )
        return True

    @property
    def mqtt_client(self):
        self.test_mqtt_settings()
        if self._mqtt_client is None:
            self._mqtt_client = MQTTClient(
                octoprint_device_id=self.octoprint_device_id,
                cloudiot_device_id=self.cloudiot_device_id,
                private_key_file=self.device_private_key,
                ca_cert=self.ca_cert,
                mqtt_receive_queue=self.mqtt_receive_queue,
            )
        return self._mqtt_client

    def event_is_tracked(self, event_type):
        prefix = self.plugin.octoprint_event_prefix
        prefix_stripped = event_type.replace(prefix, "")
        return (
            event_type in PrintNannyPluginEventType.allowable_values
            or prefix_stripped in PrintNannyPluginEventType.allowable_values
            or event_type in OctoPrintEventType.allowable_values
            or prefix_stripped in OctoPrintEventType.allowable_values
            or event_type in PrintJobStatusEnum.allowable_values
            or prefix_stripped in PrintJobStatusEnum.allowable_values
            or event_type in RemoteCommandEventType.allowable_values
            or prefix_stripped in RemoteCommandEventType.allowable_values
        )
