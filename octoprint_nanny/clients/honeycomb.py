import os
import beeline
from beeline.patch.requests import *

HONEYCOMB_DATASET = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_DATASET", "print_nanny_prod"
)
HONEYCOMB_API_KEY = os.environ.get(
    "OCTOPRINT_NANNY_HONEYCOMB_API_KEY", "ef843461ea1d7b2a953fa1b68e9394da"
)
HONEYCOMB_DEBUG = os.environ.get("HONEYCOMB_DEBUG", False)


class HoneycombTracer:
    def __init__(
        self,
        service_name,
        sample_rate=1,
        max_concurrent_batches=10,
        max_batch_size=100,
        send_frequency=3,
        block_on_send=False,
        block_on_response=False,
        sampler_hook=None,
        presend_hook=None,
        debug=HONEYCOMB_DEBUG,
    ):

        self.service_name = service_name
        self.sample_rate = sample_rate
        self.max_concurrent_batches = max_concurrent_batches
        self.max_batch_size = max_batch_size
        self.send_frequency = send_frequency
        self.block_on_send = block_on_send
        self.block_on_response = block_on_response
        self.sampler_hook = sampler_hook
        self.present_hook = presend_hook
        self.debug = debug

        beeline.init(
            writekey=HONEYCOMB_API_KEY,
            dataset=HONEYCOMB_DATASET,
            service_name=service_name,
            debug=debug,
        )
        self.context = {}

    def add_global_context(self, context):
        """
        Context will be added to each trace
        """
        self.context.update(context)
        return self.context

    def add_context(self, context: dict):
        """
        Add context field to the currently active span
        """
        return beeline.add_context(context)

    def add_context_field(self, name, value):
        """
        Add a context field to active span by name
        """
        return beeline.add_context_field(name, value)

    def add_rollup_field(self, name, value):
        """
        Rollup fields are aggregated (summed) if the same key/value pair appears repeatedly
        """
        return beeline.add_rollup_field(name, value)

    def add_trace_field(self, name, value):
        """
        Adds a field to the current trace span, in addition to all future spans
        """
        return beeline.add_trace_field(name, value)

    def start_trace(self):

        beeline.add_context(self.context)

        return beeline.start_trace()

    def finish_trace(self, trace):
        return beeline.finish_trace(trace)

    def on_shutdown(self):
        return beeline.close()
