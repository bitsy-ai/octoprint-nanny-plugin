import aiohttp
import logging
import urllib
import hashlib
import backoff

from octoprint.events import Events

import print_nanny_client
from print_nanny_client import ApiClient as AsyncApiClient

from print_nanny_client.api.events_api import EventsApi
from print_nanny_client.api.remote_control_api import RemoteControlApi
from print_nanny_client.api.users_api import UsersApi
from print_nanny_client.models.octo_print_event_request import OctoPrintEventRequest
from print_nanny_client.models.print_job_request import PrintJobRequest
from print_nanny_client.models.printer_profile_request import PrinterProfileRequest
from print_nanny_client.models.octo_print_device_key_request import OctoPrintDeviceKeyRequest


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.rest")

CLIENT_EXCEPTIONS = (
    print_nanny_client.exceptions.ApiException,
    aiohttp.client_exceptions.ClientError,
)
MAX_BACKOFF_TIME = 16


class RestAPIClient:
    """
    webapp rest API calls and retry behavior
    """

    def __init__(self, auth_token, api_url):

        self.api_url = api_url
        self.auth_token = auth_token

    @property
    def _api_config(self):
        parsed_uri = urllib.parse.urlparse(self.api_url)
        host = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        config = print_nanny_client.Configuration(host=host)

        config.access_token = self.auth_token
        return config

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_or_create_octoprint_device(self, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = OctoPrintDeviceKeyRequest(**kwargs)
            api_instance = RemoteControlApi(api_client=api_client)
            octoprint_device = await api_instance.octoprint_devices_update_or_create(
                request
            )
            return octoprint_device

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_octoprint_device(self, octoprint_device_id, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            api_client.client_side_validation = False
            request = OctoPrintDeviceRequest(**kwargs)
            api_instance = RemoteControlApi(api_client=api_client)
            octoprint_device = await api_instance.octoprint_devices_partial_update(
                octoprint_device_id, request
            )
            return octoprint_device

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def get_telemetry_events(self):
        async with AsyncApiClient(self._api_config) as api_client:
            api_client.client_side_validation = False
            telemetry_events = await EventsApi(
                api_client
            ).octoprint_events_telemetry_retrieve()
            logger.info(
                f"OctoPrint events forwarded to mqtt telemetry topic {telemetry_events}"
            )
            return telemetry_events

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def get_user(self):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = UsersApi(api_client=api_client)
            user = await api_instance.users_me_retrieve()
            return user

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def create_octoprint_event(self, event_type, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = EventsApi(api_client=api_client)
            request = OctoPrintEventRequest(
                dt=event_data["metadata"]["dt"],
                event_type=event_type,
                event_data=event_data,
                plugin_version=event_data["metadata"]["plugin_version"],
                octoprint_version=event_data["metadata"]["octoprint_version"],
            )
            return await api_instance.octoprint_events_create(request)

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_print_progress(self, print_job_id, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            request = (
                print_nanny_client.models.print_job_request.PatchedPrintJobRequest(
                    progress=event_data["progress"]
                )
            )
            api_instance = RemoteControlApi(api_client=api_client)
            print_job = await api_instance.print_jobs_partial_update(
                print_job_id, patched_print_job_request=request
            )
            return print_job

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_or_create_gcode_file(self, event_data, gcode_file_path):
        gcode_f = open(gcode_file_path, "rb")
        file_hash = hashlib.md5(gcode_f.read()).hexdigest()
        gcode_f.seek(0)
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)

            gcode_file = await api_instance.gcode_files_update_or_create(
                name=event_data["name"],
                file_hash=file_hash,
                file=gcode_f,
            )
            logger.info(f"Upserted gcode_file {gcode_file}")
            return gcode_file

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def create_print_job(self, event_data, gcode_file_id, printer_profile_id):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            request = print_nanny_client.models.print_job_request.PrintJobRequest(
                gcode_file=gcode_file_id,
                dt=event_data["dt"],
                name=event_data["name"],
                printer_profile=printer_profile_id,
            )
            print_job = await api_instance.print_jobs_create(request)
            return print_job

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_or_create_printer_profile(self, event_data):

        async with AsyncApiClient(self._api_config) as api_client:
            # printer profile
            api_instance = RemoteControlApi(api_client=api_client)
            request = PrinterProfileRequest(
                axes_e_inverted=event_data["printer_profile"]["axes"]["e"]["inverted"],
                axes_x_inverted=event_data["printer_profile"]["axes"]["x"]["inverted"],
                axes_y_inverted=event_data["printer_profile"]["axes"]["y"]["inverted"],
                axes_z_inverted=event_data["printer_profile"]["axes"]["z"]["inverted"],
                axes_e_speed=event_data["printer_profile"]["axes"]["e"]["speed"],
                axes_x_speed=event_data["printer_profile"]["axes"]["x"]["speed"],
                axes_y_speed=event_data["printer_profile"]["axes"]["y"]["speed"],
                axes_z_speed=event_data["printer_profile"]["axes"]["z"]["speed"],
                extruder_count=event_data["printer_profile"]["extruder"]["count"],
                extruder_nozzle_diameter=event_data["printer_profile"]["extruder"][
                    "nozzleDiameter"
                ],
                extruder_shared_nozzle=event_data["printer_profile"]["extruder"][
                    "sharedNozzle"
                ],
                name=event_data["printer_profile"]["name"],
                model=event_data["printer_profile"]["model"],
                heated_bed=event_data["printer_profile"]["heatedBed"],
                heated_chamber=event_data["printer_profile"]["heatedChamber"],
                volume_custom_box=event_data["printer_profile"]["volume"]["custom_box"],
                volume_depth=event_data["printer_profile"]["volume"]["depth"],
                volume_formfactor=event_data["printer_profile"]["volume"]["formFactor"],
                volume_height=event_data["printer_profile"]["volume"]["height"],
                volume_origin=event_data["printer_profile"]["volume"]["origin"],
                volume_width=event_data["printer_profile"]["volume"]["width"],
            )
            printer_profile = await api_instance.printer_profiles_update_or_create(
                request
            )
            return printer_profile

    def _printer_profile_request(self, data):
        """
        data: https://docs.octoprint.org/en/master/api/printerprofiles.html
        """
        return PrinterProfileRequest(
            axes_e_inverted=data["printer_profile"]["axes"]["e"]["inverted"],
            axes_x_inverted=data["printer_profile"]["axes"]["x"]["inverted"],
            axes_y_inverted=data["printer_profile"]["axes"]["y"]["inverted"],
            axes_z_inverted=data["printer_profile"]["axes"]["z"]["inverted"],
            axes_e_speed=data["printer_profile"]["axes"]["e"]["speed"],
            axes_x_speed=data["printer_profile"]["axes"]["x"]["speed"],
            axes_y_speed=data["printer_profile"]["axes"]["y"]["speed"],
            axes_z_speed=data["printer_profile"]["axes"]["z"]["speed"],
            extruder_count=data["printer_profile"]["extruder"]["count"],
            extruder_nozzle_diameter=data["printer_profile"]["extruder"][
                "nozzleDiameter"
            ],
            extruder_shared_nozzle=data["printer_profile"]["extruder"]["sharedNozzle"],
            octoprint_id=data["printer_profile"]["id"],
            name=data["printer_profile"]["name"],
            model=data["printer_profile"]["model"],
            heated_bed=data["printer_profile"]["heatedBed"],
            heated_chamber=data["printer_profile"]["heatedChamber"],
            volume_custom_box=data["printer_profile"]["volume"]["custom_box"],
            volume_depth=data["printer_profile"]["volume"]["depth"],
            volume_formfactor=data["printer_profile"]["volume"]["formFactor"],
            volume_height=data["printer_profile"]["volume"]["height"],
            volume_origin=data["printer_profile"]["volume"]["origin"],
            volume_width=data["printer_profile"]["volume"]["width"],
        )

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def update_or_create_printer_profile(self, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            # printer profile
            api_instance = RemoteControlApi(api_client=api_client)
            request = self._printer_profile_request(event_data)
            printer_profile = await api_instance.printer_profiles_update_or_create(
                request
            )
            return printer_profile
