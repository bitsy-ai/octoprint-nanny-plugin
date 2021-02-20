import aiohttp
import logging
import urllib
import hashlib
import backoff
import json
import beeline

from octoprint.events import Events

from octoprint_nanny.clients.honeycomb import HoneycombTracer
import print_nanny_client
from print_nanny_client import ApiClient as AsyncApiClient

from print_nanny_client.api.events_api import EventsApi
from print_nanny_client.api.remote_control_api import RemoteControlApi
from print_nanny_client.api.users_api import UsersApi
from print_nanny_client.models.octo_print_event_request import OctoPrintEventRequest
from print_nanny_client.models.print_job_request import PrintJobRequest
from print_nanny_client.models.printer_profile_request import PrinterProfileRequest
from print_nanny_client.models.octo_print_device_request import (
    OctoPrintDeviceRequest,
)
from octoprint_nanny.utils.encoder import NumpyEncoder


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.rest")

API_CLIENT_EXCEPTIONS = (
    print_nanny_client.exceptions.ApiException,
    aiohttp.client_exceptions.ClientError,
)
MAX_BACKOFF_TIME = 16


class RestAPIClient:
    """
    webapp rest API calls and retry behavior
    """

    def __init__(self, auth_token: str, api_url: str):
        self.api_url = api_url
        self.auth_token = auth_token
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

    @property
    def _api_config(self):
        parsed_uri = urllib.parse.urlparse(self.api_url)
        host = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        config = print_nanny_client.Configuration(host=host)

        config.access_token = self.auth_token
        return config

    @beeline.traced("RestAPIClient.update_or_create_octoprint_device")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
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
    )
    async def update_octoprint_device(self, device_id, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = print_nanny_client.PatchedOctoPrintDeviceRequest(**kwargs)

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
    )
    async def update_remote_control_command(self, command_id, **kwargs):
        async with AsyncApiClient(self._api_config) as api_client:
            request = print_nanny_client.models.PatchedRemoteControlCommandRequest(
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
    )
    async def create_octoprint_event(self, event_type, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = EventsApi(api_client=api_client)
            request = OctoPrintEventRequest(
                created_dt=event_data["metadata"]["created_dt"],
                event_type=event_type,
                event_data=event_data,
                plugin_version=event_data["metadata"]["plugin_version"],
                octoprint_version=event_data["metadata"]["octoprint_version"],
            )
            return await api_instance.octoprint_events_create(request)

    @beeline.traced("RestAPIClient.update_print_progress")
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

    @beeline.traced("RestAPIClient.update_or_create_gcode_file")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
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

    @beeline.traced("RestAPIClient.create_snapshot")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def create_snapshot(self, image, command):
        image.name = str(command) + ".jpg"
        image.seek(0)
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            # https://github.com/aio-libs/aiohttp/issues/3652
            # in a multi-part form request (file upload), params MUST be serialized as strings and deserialized to integers on the server-side
            snapshot = await api_instance.snapshots_create(
                image=image,
                command=str(command),
            )
            logger.info(f"Created snapshot {snapshot}")
            return snapshot

    @beeline.traced("RestAPIClient.create_print_job")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
    )
    async def create_print_job(
        self, event_data, gcode_file_id, printer_profile_id, octoprint_device_id
    ):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = RemoteControlApi(api_client=api_client)
            request = print_nanny_client.models.print_job_request.PrintJobRequest(
                gcode_file=gcode_file_id,
                name=event_data["name"],
                printer_profile=printer_profile_id,
                octoprint_device=octoprint_device_id,
            )
            print_job = await api_instance.print_jobs_create(request)
            return print_job

    @beeline.traced("RestAPIClient.update_or_create_printer_profile")
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        logger=logger,
        max_time=MAX_BACKOFF_TIME,
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
    )
    async def update_or_create_device_calibration(
        self, octoprint_device_id, coordinates, mask
    ):
        mask = json.dumps(mask, cls=NumpyEncoder)
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = print_nanny_client.MlOpsApi(api_client=api_client)

            request = print_nanny_client.DeviceCalibrationRequest(
                octoprint_device=octoprint_device_id, coordinates=coordinates, mask=mask
            )
            device_calibration = await api_instance.device_calibration_update_or_create(
                request
            )
            return device_calibration
