import aiohttp
import logging
import urllib.parse
import backoff
import os
from typing import Optional

import printnanny_api_client
from printnanny_api_client import ApiClient as AsyncApiClient
from printnanny_api_client.api.accounts_api import AccountsApi

from octoprint_nanny.env import MAX_BACKOFF_TIME

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.rest")

API_CLIENT_EXCEPTIONS = (
    printnanny_api_client.exceptions.ApiException,
    aiohttp.client_exceptions.ClientError,
)


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


class PrintNannyCloudAPIClient:
    """
    webapp rest API calls and retry behavior
    """

    def __init__(self, base_path: str, bearer_access_token: Optional[str] = None):
        self.base_path = base_path
        self.bearer_access_token = bearer_access_token

    @property
    def _api_config(self):
        parsed_uri = urllib.parse.urlparse(self.base_path)
        host = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        config = printnanny_api_client.Configuration(host=host)

        config.access_token = self.bearer_access_token
        return config

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
            api_instance = AccountsApi(api_client=api_client)
            user = await api_instance.accounts_user_retrieve()
            return user

    # @backoff.on_exception(
    #     backoff.expo,
    #     aiohttp.ClientConnectionError,
    #     logger=logger,
    #     max_time=MAX_BACKOFF_TIME,
    #     jitter=backoff.random_jitter,
    #     giveup=fatal_code,
    #     on_backoff=backoff_hdlr,
    #     on_giveup=giveup_hdlr,
    # )
    # async def update_or_create_printer_profile(
    #     self, printer_profile, octoprint_device_id
    # ):
    #     """
    #     https://github.com/OctoPrint/OctoPrint/blob/f67c15a9a47794a68be9aed4f2d5a12a87e70179/src/octoprint/printer/profile.py#L46
    #     """

    #     async with AsyncApiClient(self._api_config) as api_client:
    #         # printer profile
    #         # TODO re-enable with OctoPrintApi module
    #         # api_instance = RemoteControlApi(api_client=api_client)

    #         # cooerce duck-typed fields
    #         if type(printer_profile["volume"]["custom_box"]) is bool:
    #             volume_custom_box = {}
    #         else:
    #             volume_custom_box = printer_profile["volume"]["custom_box"]

    #         request = PrinterProfileRequest(
    #             octoprint_device=octoprint_device_id,
    #             octoprint_key=printer_profile["id"],
    #             axes_e_inverted=printer_profile["axes"]["e"]["inverted"],
    #             axes_x_inverted=printer_profile["axes"]["x"]["inverted"],
    #             axes_y_inverted=printer_profile["axes"]["y"]["inverted"],
    #             axes_z_inverted=printer_profile["axes"]["z"]["inverted"],
    #             axes_e_speed=printer_profile["axes"]["e"]["speed"],
    #             axes_x_speed=printer_profile["axes"]["x"]["speed"],
    #             axes_y_speed=printer_profile["axes"]["y"]["speed"],
    #             axes_z_speed=printer_profile["axes"]["z"]["speed"],
    #             extruder_count=printer_profile["extruder"]["count"],
    #             extruder_nozzle_diameter=printer_profile["extruder"]["nozzleDiameter"],
    #             extruder_shared_nozzle=printer_profile["extruder"]["sharedNozzle"],
    #             name=printer_profile["name"],
    #             model=printer_profile["model"],
    #             heated_bed=printer_profile["heatedBed"],
    #             heated_chamber=printer_profile["heatedChamber"],
    #             volume_custom_box=volume_custom_box,
    #             volume_depth=printer_profile["volume"]["depth"],
    #             volume_formfactor=printer_profile["volume"]["formFactor"],
    #             volume_height=printer_profile["volume"]["height"],
    #             volume_origin=printer_profile["volume"]["origin"],
    #             volume_width=printer_profile["volume"]["width"],
    #         )
    #         printer_profile = await api_instance.printer_profiles_update_or_create(
    #             request
    #         )
    #         return printer_profile

    async def create_backup(
        self, hostname: str, name: str, octoprint_version: str, file: str
    ):
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = printnanny_api_client.OctoprintApi(api_client=api_client)

            backup = await api_instance.octoprint_backups_create(
                hostname,
                name,
                octoprint_version,
                file,
            )
            return backup
