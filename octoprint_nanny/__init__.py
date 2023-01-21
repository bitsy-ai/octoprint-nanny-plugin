# type: ignore
from __future__ import absolute_import

__plugin_name__ = "OctoPrint-Nanny"

__plugin_pythoncompat__ = ">=3,<4"  # only python 3

__plugin_version__ = "0.15.9"


def __plugin_load__():
    from .plugins import OctoPrintNannyPlugin

    global __plugin_implementation__
    __plugin_implementation__ = OctoPrintNannyPlugin()
    __plugin_implementation__.version = __plugin_version__
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
    }
