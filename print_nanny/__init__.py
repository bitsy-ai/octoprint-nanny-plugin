# coding=utf-8
from __future__ import absolute_import

import logging


from .plugins import BitsyNannyPlugin


logger = logging.getLogger('octoprint.plugins.print_nanny')
     
        
        
def _register_custom_events(*args, **kwargs):
    return [
        "predict_done", 
        "predict_failed", 
        "upload_done", 
        "upload_failed"
    ]

__plugin_name__ = "Bitsy Print Nanny"

__plugin_pythoncompat__ = ">=3,<4" # only python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = BitsyNannyPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.timelapse.capture.post": __plugin_implementation__.on_timelapse_capture
    }

