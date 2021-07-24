import os
import beeline
from beeline.patch.requests import *

HONEYCOMB_DATASET = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_DATASET", "print_nanny_plugin_prod"
)
HONEYCOMB_API_KEY = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_API_KEY", "84ed521e04aad193f543d5a078ad2708"
)
HONEYCOMB_DEBUG = os.environ.get("HONEYCOMB_DEBUG", False)

beeline.init(
    writekey=HONEYCOMB_API_KEY,
    dataset=HONEYCOMB_DATASET,
    service_name="plugin",
    debug=HONEYCOMB_DEBUG,
)
