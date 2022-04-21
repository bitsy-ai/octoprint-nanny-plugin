# type: ignore
from __future__ import absolute_import

from .plugins import OctoPrintNannyPlugin

__plugin_name__ = "OctoPrint Nanny"

__plugin_pythoncompat__ = ">=3,<4"  # only python 3

__plugin_version__ = "0.10.0rc3"


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
