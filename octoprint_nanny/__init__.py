# coding=utf-8
from __future__ import absolute_import

import logging


from .plugins import OctoPrintNannyPlugin


logger = logging.getLogger("octoprint.plugins.octoprint_nanny")


__plugin_name__ = "Print Nanny"

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
