import aiohttp
import logging
from urllib import urlparse

import hashlib
import backoff

import print_nanny_client
from print_nanny_client import ApiClient as AsyncApiClient
from print_nanny_client.api.events_api import EventsApi
from print_nanny_client.api.remote_control_api import RemoteControlApi
from print_nanny_client.api.users_api import UsersApi
from print_nanny_client.models.octo_print_event_request import OctoPrintEventRequest
from print_nanny_client.models.print_job_request import PrintJobRequest
from print_nanny_client.models.printer_profile_request import PrinterProfileRequest


logger = logging.getLogger("octoprint.plugins.print_nanny.rest_clientt")


class RestAPIClient:
    """
    webapp rest API calls and retry behavior
    """

    def __init__(self, auth_token=None, api_url=None):

        self.api_url = api_url
        self.auth_token = auth_token

    @property
    def _api_config(self):
        parsed_uri = urlparse(self.api_url)
        host = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        config = print_nanny_client.Configuration(host=host)

        config.access_token = self.auth_token
        return config

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def get_tracking_events(self):
        async with AsyncApiClient(self._api_config) as api_client:
            api_client.client_side_validation = False
            tracking_events = await EventsApi(
                api_client
            ).octoprint_events_tracking_retrieve()
            logging.info(f"Tracking octoprint events {self._tracking_events}")
            return tracking_events

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def get_user(self):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = UsersApi(api_client=api_client)
            user = await api_instance.users_me_retrieve()
            return user

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def create_octoprint_event(self, event_type, event_data):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = EventsApi(api_client=api_client)
            request = OctoPrintEventRequest(
                dt=event_data["metadata"]["dt"],
                event_type=event_type,
                event_data=event_data,
                plugin_version=event_type["plugin_version"],
                octoprint_version=event_data["metadata"]["octoprint_version"],
            )
            return await api_instance.octoprint_events_create(request)

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def update_print_progress(print_job_id, event_data):
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

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def update_or_create_gcode_file(self, event_data, gcode_file_path):
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

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def create_print_job(self, event_data, gcode_file_id, printer_profile_id):
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

    @backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, logger=logger)
    def update_or_create_printer_profile(self, event_data):

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
