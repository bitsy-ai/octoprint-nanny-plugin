import aiohttp
import logging
import urllib
import hashlib
import backoff
import os
import beeline

import printnanny_api_client
from printnanny_api_client import ApiClient as AsyncApiClient

from printnanny_api_client.api.telemetry_api import TelemetryApi
from printnanny_api_client.api.remote_control_api import RemoteControlApi
from printnanny_api_client.api.users_api import UsersApi
from printnanny_api_client.models.octo_print_event_request import OctoPrintEventRequest
from printnanny_api_client.models.printer_profile_request import PrinterProfileRequest
from printnanny_api_client.models.octo_print_device_request import (
    OctoPrintDeviceRequest,
)
from octoprint_nanny.utils.encoder import JSONEncoder


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.rest")

API_CLIENT_EXCEPTIONS = (
    printnanny_api_client.exceptions.ApiException,
    aiohttp.client_exceptions.ClientError,
)
MAX_BACKOFF_TIME = int(os.environ.get("OCTOPRINT_NANNY_MAX_BACKOFF_TIME", 120))

logger.info(f"OCTOPRINT_NANNY_MAX_BACKOFF_TIME={MAX_BACKOFF_TIME}")


def fatal_code(e) -> bool:
    """
    Returns True if error code is fatal and should not be retried
    """
    if isinstance(e, aiohttp.ClientConnectionError):
        return False
    return 400 <= e.response.status_code < 500


def backoff_hdlr(details):
    logger.warning(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


def giveup_hdlr(details):
    logger.error(
        "Giving up {elapsed:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


class RestAPIClient:
    """
    webapp rest API calls and retry behavior
    """

    def __init__(self, auth_token: str, api_url: str):
        self.api_url = api_url
        self.auth_token = auth_token

    @property
    def _api_config(self):
        parsed_uri = urllib.parse.urlparse(self.api_url)
        host = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        config = printnanny_api_client.Configuration(host=host)

        config.access_token = self.auth_token
        return config

    @beeline.traced("RestAPIClient.update_or_create_octoprint_device")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_or_create_octoprint_device(self, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = OctoPrintDeviceRequest(**kwargs)
            api_instance = RemoteControlApi(api_client=api_client)
            octoprint_device = await api_instance.octoprint_devices_update_or_create(
                request
            )
            return octoprint_device

    @beeline.traced("RestAPIClient.update_octoprint_device")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_octoprint_device(self, device_id, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = printnanny_api_client.PatchedOctoPrintDeviceRequest(**kwargs)

            api_instance = RemoteControlApi(api_client=api_client)
            octoprint_device = await api_instance.octoprint_devices_partial_update(
                device_id, patched_octo_print_device_request=request
            )
            return octoprint_device

    @beeline.traced("RestAPIClient.update_remote_control_command")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_remote_control_command(self, command_id, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = printnanny_api_client.models.PatchedRemoteControlCommandRequest(
                **kwargs
            )
            api_instance = RemoteControlApi(api_client=api_client)
            command = await api_instance.commands_partial_update(
                command_id, patched_remote_control_command_request=request
            )
            return command

    @beeline.traced("RestAPIClient.get_user")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def get_user(self):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = UsersApi(api_client=api_client)
            user = await api_instance.users_me_retrieve()
            return user

    @beeline.traced("RestAPIClient.create_octoprint_event")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def create_octoprint_event(self, event_type, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = TelemetryApi(api_client=api_client)
            request = OctoPrintEventRequest(
                event_type=event_type,
                event_data=event_data,
                print_nanny_plugin_version=event_data["metadata"]["plugin_version"],
                octoprint_version=event_data["metadata"]["octoprint_version"],
            )
            return await api_instance.octoprint_events_create(request)

    @beeline.traced("RestAPIClient.update_or_create_gcode_file")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_or_create_gcode_file(
        self, event_data, gcode_file_path, octoprint_device_id
    ):
        gcode_f = open(gcode_file_path, "rb")
        file_hash = hashlib.md5(gcode_f.read()).hexdigest()
        gcode_f.seek(0)
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            # https://github.com/aio-libs/aiohttp/issues/3652
            # in a multi-part form request (file upload), octoprint_device is accepted as a string and deserialized to an integer on the server-side

            gcode_file = await api_instance.gcode_files_update_or_create(
                name=event_data["name"],
                file_hash=file_hash,
                file=gcode_f,
                octoprint_device=str(octoprint_device_id),
            )
            logger.info(f"Upserted gcode_file {gcode_file}")
            return gcode_file

    @beeline.traced("RestAPIClient.create_print_session")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def create_print_session(self, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            request = (
                printnanny_api_client.models.print_session_request.PrintSessionRequest(
                    **kwargs
                )
            )
            print_session = await api_instance.print_sessions_create(request)
            return print_session

    @beeline.traced("RestAPIClient.update_print_session")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_print_session(self, session: str, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            request = printnanny_api_client.models.patched_print_session_request.PatchedPrintSessionRequest(
                **kwargs
            )
            print_session = await api_instance.print_session_partial_update(
                session, patched_print_session_request=request
            )
            return print_session

    @beeline.traced("RestAPIClient.update_or_create_printer_profile")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_or_create_printer_profile(
        self, printer_profile, octoprint_device_id
    ):
        """
        https://github.com/OctoPrint/OctoPrint/blob/f67c15a9a47794a68be9aed4f2d5a12a87e70179/src/octoprint/printer/profile.py#L46
        """

        async with AsyncApiClient(self._api_config) as api_client:
            # printer profile
            api_instance = RemoteControlApi(api_client=api_client)

            # cooerce duck-typed fields
            if type(printer_profile["volume"]["custom_box"]) is bool:
                volume_custom_box = {}
            else:
                volume_custom_box = printer_profile["volume"]["custom_box"]

            request = PrinterProfileRequest(
                octoprint_device=octoprint_device_id,
                octoprint_key=printer_profile["id"],
                axes_e_inverted=printer_profile["axes"]["e"]["inverted"],
                axes_x_inverted=printer_profile["axes"]["x"]["inverted"],
                axes_y_inverted=printer_profile["axes"]["y"]["inverted"],
                axes_z_inverted=printer_profile["axes"]["z"]["inverted"],
                axes_e_speed=printer_profile["axes"]["e"]["speed"],
                axes_x_speed=printer_profile["axes"]["x"]["speed"],
                axes_y_speed=printer_profile["axes"]["y"]["speed"],
                axes_z_speed=printer_profile["axes"]["z"]["speed"],
                extruder_count=printer_profile["extruder"]["count"],
                extruder_nozzle_diameter=printer_profile["extruder"]["nozzleDiameter"],
                extruder_shared_nozzle=printer_profile["extruder"]["sharedNozzle"],
                name=printer_profile["name"],
                model=printer_profile["model"],
                heated_bed=printer_profile["heatedBed"],
                heated_chamber=printer_profile["heatedChamber"],
                volume_custom_box=volume_custom_box,
                volume_depth=printer_profile["volume"]["depth"],
                volume_formfactor=printer_profile["volume"]["formFactor"],
                volume_height=printer_profile["volume"]["height"],
                volume_origin=printer_profile["volume"]["origin"],
                volume_width=printer_profile["volume"]["width"],
            )
            printer_profile = await api_instance.printer_profiles_update_or_create(
                request
            )
            return printer_profile

    @beeline.traced("RestAPIClient.update_or_create_device_calibration")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
        jitter=backoff.random_jitter,
        giveup=fatal_code,
        on_backoff=backoff_hdlr,
        on_giveup=giveup_hdlr,
    )
    async def update_or_create_device_calibration(self, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = printnanny_api_client.MlOpsApi(api_client=api_client)

            request = printnanny_api_client.DeviceCalibrationRequest(**kwargs)
            device_calibration = await api_instance.device_calibration_update_or_create(
                request
            )
            return device_calibration

    async def create_backup(
        self, hostname: str, name: str, octoprint_version: str, file: str
    ):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = printnanny_api_client.OctoprintBackupsApi(
                api_client=api_client
            )

            backup = await api_instance.octoprint_backups_create(
                hostname,
                name,
                octoprint_version,
                file,
            )
            return backup
