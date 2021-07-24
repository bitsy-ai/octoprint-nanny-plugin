import hashlib
import math
import os
import struct

import beeline
from beeline.patch.requests import *

HONEYCOMB_DATASET = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_DATASET", "print_nanny_plugin_prod"
)
HONEYCOMB_API_KEY = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_API_KEY", "84ed521e04aad193f543d5a078ad2708"
)
HONEYCOMB_DEBUG = os.environ.get("HONEYCOMB_DEBUG", False)

# ref: https://docs.honeycomb.io/getting-data-in/python/beeline/#customizing-sampling-logic
MAX_INT32 = math.pow(2, 32) - 1

# Deterministic _should_sample taken from https://github.com/honeycombio/beeline-python/blob/1ffe66ed1779143592edf9227d3171cb805216b6/beeline/trace.py#L258-L267
def _should_sample(trace_id, sample_rate):
    sample_upper_bound = MAX_INT32 / sample_rate
    sha1 = hashlib.sha1()
    sha1.update(trace_id.encode("utf-8"))
    # convert last 4 digits to int
    (value,) = struct.unpack("<I", sha1.digest()[-4:])
    return value < sample_upper_bound


def honeycomb_event_sampler(fields):
    # our default sample rate, sample one in every 10 events
    sample_rate = 10

    response_code = fields.get("response.status_code")
    # False indicates that we should not keep this event
    if response_code == 302:
        return False, 0
    elif response_code == 200:
        # heavily sample healthy requests
        sample_rate = 100
    elif response_code >= 500:
        # sample every error request
        sample_rate = 1

    # The truthiness of the first return argument determines whether we keep the
    # event. The second argument, the sample rate, tells Honeycomb what rate the
    # event was sampled at (important to correctly weight calculations on the data).
    trace_id = fields.get("trace.trace_id")
    if _should_sample(trace_id, sample_rate):
        return True, sample_rate
    return False, 0


beeline.init(
    writekey=HONEYCOMB_API_KEY,
    dataset=HONEYCOMB_DATASET,
    service_name="plugin",
    debug=HONEYCOMB_DEBUG,
    sampler_hook=honeycomb_event_sampler,
)
