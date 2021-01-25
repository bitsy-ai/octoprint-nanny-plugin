# coding=utf-8
from __future__ import absolute_import

import logging
import os
import pathlib

site_package_dir = pathlib.Path(__file__).parent.absolute()
c_libs = os.path.join(site_package_dir, "lib/")
##
# Add lib/ to LD_LIBRARY_PATH
##

LD_LIBRARY_PATH = os.environ.get("LD_LIBRARY_PATH")

if LD_LIBRARY_PATH is None:
    os.environ["LD_LIBRARY_PATH"] = c_libs
else:
    os.environ["LD_LIBRARY_PATH"] = "{}:{}".format(
        (os.environ["LD_LIBRARY_PATH"], c_libs)
    )

from .plugins import OctoPrintNannyPlugin


logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


__plugin_name__ = "OctoPrint Nanny"

__plugin_pythoncompat__ = ">=3,<4"  # only python 3

__plugin_version__ = "0.1.0"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctoPrintNannyPlugin()

    __plugin_implementation__.version = __plugin_version__

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        # "octoprint.timelapse.capture.post": __plugin_implementation__.on_timelapse_capture,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
        # "octoprint.server.http.routes": __plugin_implementation__.register_custom_routes
    }
