from datetime import datetime, timedelta
import ssl
import jwt
import gzip
import logging
import os
import time
import json
import io
import random
import paho.mqtt.client as mqtt
from typing import List
import sys
import beeline

from octoprint_nanny.utils.encoder import NumpyEncoder
from octoprint_nanny.clients.honeycomb import HoneycombTracer


JWT_EXPIRES_MINUTES = os.environ.get("OCTOPRINT_NANNY_MQTT_JWT_EXPIRES_MINUTES", 1380)
GCP_PROJECT_ID = os.environ.get("OCTOPRINT_NANNY_GCP_PROJECT_ID", "print-nanny")
MQTT_BRIDGE_HOSTNAME = os.environ.get(
    "OCTOPRINT_NANNY_MQTT_BRIDGE_HOSTNAME", "mqtt.2030.ltsapis.goog"
)

MQTT_BRIDGE_PORT = os.environ.get("OCTOPRINT_NANNY_MQTT_BRIDGE_PORT", 443)
IOT_DEVICE_REGISTRY = os.environ.get(
    "OCTOPRINT_NANNY_IOT_DEVICE_REGISTRY", "devices-us-central1-prod"
)
IOT_DEVICE_REGISTRY_REGION = os.environ.get(
    "OCTOPRINT_NANNY_IOT_DEVICE_REGISTRY_REGION", "us-central1"
)

OCTOPRINT_EVENT_FOLDER = "octoprint-events"
POST_EVENT_FOLDER = "monitoring-frame-post"
RAW_EVENT_FOLDER = "monitoring-frame-raw"
ACTIVE_LEARNING_EVENT_FOLDER = "active-learning"

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.mqtt")
device_logger = logging.getLogger(
    "octoprint.plugins.octoprint_nanny.clients.mqtt.device"
)

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 300

# Whether to wait with exponential backoff before publishing.
should_backoff = False


class MQTTClient:
    def __init__(
        self,
        device_id: str,
        device_cloudiot_id: str,
        private_key_file: str,
        ca_cert: str,
        algorithm="ES256",
        mqtt_receive_queue=None,
        mqtt_bridge_hostname=MQTT_BRIDGE_HOSTNAME,
        mqtt_bridge_port=MQTT_BRIDGE_PORT,
        on_connect=None,
        on_disconnect=None,
        on_log=None,
        on_message=None,
        on_publish=None,
        on_subscribe=None,
        on_unsubscribe=None,
        project_id=GCP_PROJECT_ID,
        region=IOT_DEVICE_REGISTRY_REGION,
        registry_id=IOT_DEVICE_REGISTRY,
        keepalive=900,
        trace_context={},
        message_callbacks=[],  # see message_callback_add() https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#subscribe-unsubscribe
    ):
        self.device_id = device_cloudiot_id
        self.device_cloudiot_id = device_cloudiot_id
        client_id = f"projects/{project_id}/locations/{region}/registries/{registry_id}/devices/{device_cloudiot_id}"

        self.client_id = client_id
        self.private_key_file = private_key_file
        self.algorithm = algorithm
        self.project_id = project_id
        self.mqtt_bridge_hostname = mqtt_bridge_hostname
        self.mqtt_bridge_port = mqtt_bridge_port
        self.region = region
        self.registry_id = registry_id
        self.keepalive = keepalive

        self.ca_cert = ca_cert

        self.region = region
        self.algorithm = algorithm

        self.mqtt_receive_queue = mqtt_receive_queue
        self._honeycomb_tracer = HoneycombTracer(service_name="octoprint_plugin")

        self.client = mqtt.Client(client_id=client_id)
        logger.info(f"Initializing MQTTClient from {locals()}")

        # register callback functions
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe

        # device receives configuration updates on this topic
        self.config_topic = f"/devices/{self.device_cloudiot_id}/config"

        # device receives commands on this topic
        self.commands_topic = f"/devices/{self.device_cloudiot_id}/commands/#"
        # remote_control app commmands are routed to this subfolder
        self.remote_control_commands_topic = (
            f"/devices/{self.device_cloudiot_id}/commands/remote_control"
        )
        # this permits routing on a per-app basis, e.g.
        # /devices/{self.device_cloudiot_id}/commands/my_app_name

        # default telemetry topic
        self.default_telemetry_topic = f"/devices/{self.device_cloudiot_id}/events"

        # octoprint event telemetry topic
        self.octoprint_event_topic = os.path.join(
            self.default_telemetry_topic, OCTOPRINT_EVENT_FOLDER
        )
        # bounding box telemetry topic
        self.monitoring_frame_post_topic = os.path.join(
            self.default_telemetry_topic, POST_EVENT_FOLDER
        )
        # active learning telemetry topic
        self.monitoring_frame_raw_topic = os.path.join(
            self.default_telemetry_topic, RAW_EVENT_FOLDER
        )

    ###
    #   callbacks
    ##
    @beeline.traced("MQTTClient._on_message")
    def _on_message(self, client, userdata, message):
        if message.topic == self.remote_control_commands_topic:
            parsed_message = json.loads(message.payload.decode("utf-8"))
            logger.info(
                f"Received remote control command on topic={message.topic} payload={parsed_message}"
            )
            self.mqtt_receive_queue.put_nowait(
                {"topic": self.remote_control_commands_topic, "message": parsed_message}
            )
            # callback to api to indicate command was received
        elif message.topic == self.config_topic:
            try:
                parsed_message = message.payload.decode("utf-8")
                parsed_message = json.loads(parsed_message)
                logger.info(
                    f"Received config update on topic={message.topic} payload={parsed_message}"
                )
                self.mqtt_receive_queue.put_nowait(
                    {"topic": self.config_topic, "message": parsed_message}
                )
            except json.decoder.JSONDecodeError:
                logger.error(
                    f"Failed to decode message on topic={message.topic} payload={message.payload} message={parsed_message}"
                )
        else:
            logger.info(
                f"MQTTClient._on_message called with userdata={userdata} topic={message.topic} payload={message}"
            )

    def _on_publish(self, client, userdata, mid):
        logger.debug(
            f"MQTTClient._on_published called with userdata={userdata} mid={mid}"
        )

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        logger.debug(
            f"MQTTClient._on_subscribe called with userdata={userdata} mid={mid} granted_qos={granted_qos}"
        )

    def _on_unsubscribe(self, client, userdata, mid):
        logger.debug(
            f"MQTTClient.on_unsubscribe called with userdata={userdata} mid={mid}"
        )

    def _on_log(self, client, userdata, level, buf):
        getattr(device_logger, level)(buf)

    @beeline.traced("MQTTClient._on_connect")
    def _on_connect(self, client, userdata, flags, rc):
        """
        reason codes:
        0 connection successful
        1 connection refused - incorrect protocol version
        2 connection refused - invalid client id
        3 connection refused - server unavailable
        4 connection refused - bad username / password
        5 connection refused - not authorized
        6-255 unused
        """

        logger.info(
            f"MQTTClient._on_connect called with client={client} userdata={userdata} rc={rc} reason={mqtt.error_string(rc)}"
        )

        if rc == 0:
            global should_backoff
            global minimum_backoff_time
            should_backoff = False
            minimum_backoff_time = 1
            logger.info("Device successfully connected to MQTT broker")
            self.client.subscribe(self.config_topic, qos=1)
            logger.info(
                f"Subscribing to config updates device_cloudiot_id={self.device_cloudiot_id} to topic {self.config_topic}"
            )
            self.client.subscribe(self.commands_topic, qos=1)
            logger.info(
                f"Subscribing to remote commands device_cloudiot_id={self.device_cloudiot_id} to topic {self.commands_topic}"
            )
        else:
            logger.error(f"Connection refused by MQTT broker with reason code rc={rc}")

    @beeline.traced("MQTTClient._on_disconnect")
    def _on_disconnect(self, client, userdata, rc):
        logger.warning(
            f"Device disconnected from MQTT bridge client={client} userdata={userdata} rc={rc}"
        )
        # Since a disconnect occurred, the next loop iteration will wait with
        # exponential backoff.
        global should_backoff
        global minimum_backoff_time
        should_backoff = True
        if not self._thread_halt.is_set():
            if should_backoff:

                # Otherwise, wait and connect again.
                jitter = random.randint(0, 1000) / 1000.0
                delay = min(
                    minimum_backoff_time + jitter, MAXIMUM_BACKOFF_TIME + jitter
                )
                logger.info("Waiting for {} before reconnecting.".format(delay))
                time.sleep(delay)
                if minimum_backoff_time <= MAXIMUM_BACKOFF_TIME:
                    minimum_backoff_time *= 2
            self.client.reconnect()

    @beeline.traced("MQTTClient.connect")
    def connect(self):
        # configure tls
        self.client.tls_set(
            ca_certs=self.ca_cert,
            ciphers="ECDHE-RSA-AES128-GCM-SHA256",
            tls_version=ssl.PROTOCOL_TLS,
        )
        self.client.username_pw_set(
            username="unused",
            password=create_jwt(self.project_id, self.private_key_file, self.algorithm),
        )
        self.client.connect(
            self.mqtt_bridge_hostname, self.mqtt_bridge_port, keepalive=self.keepalive
        )
        logger.info(f"MQTT client connected to {self.mqtt_bridge_hostname}")

    def publish(self, payload, topic=None, retain=False, qos=1):

        """
        topic
        the topic that the message should be published on
        payload
        the actual message to send. If not given, or set to None a zero length message will be used. Passing an int or float will result in the payload being converted to a string representing that number. If you wish to send a true int/float, use struct.pack() to create the payload you require
        qos
        the quality of service level to use
        retain
        if set to True, the message will be set as the "last known good"/retained message for the topic.
        """
        if topic is None:
            topic = self.default_telemetry_topic

        return self.client.publish(topic, payload, qos=qos, retain=retain)

    @beeline.traced("MQTTClient.publish_octoprint_event")
    def publish_octoprint_event(self, event, retain=False, qos=1):
        payload = json.dumps(event, cls=NumpyEncoder)
        return self.publish(
            payload, topic=self.octoprint_event_topic, retain=retain, qos=qos
        )

    @beeline.traced("MQTTClient.publish_monitoring_frame_post")
    def publish_monitoring_frame_post(self, event, retain=False, qos=1):
        logger.debug(
            f"Publishing msg size={sys.getsizeof(event)} topic={self.monitoring_frame_post_topic}"
        )
        return self.publish(
            event, topic=self.monitoring_frame_post_topic, retain=retain, qos=qos
        )

    @beeline.traced("MQTTClient.publish_monitoring_frame_raw")
    def publish_monitoring_frame_raw(self, event, retain=False, qos=1):

        logger.debug(
            f"Publishing msg size={sys.getsizeof(event)} topic={self.monitoring_frame_raw_topic}"
        )
        return self.publish(
            event, topic=self.monitoring_frame_raw_topic, retain=retain, qos=qos
        )

    @beeline.traced("MQTTClient.stop")
    def stop(self):
        return self.client.loop_stop()

    @beeline.traced("MQTTClient.run")
    def run(self, halt):
        self._thread_halt = halt
        self.connect()
        return self.client.loop_start()


def create_jwt(
    project_id, private_key_file, algorithm, jwt_expires_minutes=JWT_EXPIRES_MINUTES
):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
    Args:
     project_id: The cloud project ID this device belongs to
     private_key_file: A path to a file containing either an RSA256 or
             ES256 private key.
     algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
    Returns:
        A JWT generated from the given project_id and private key, which
        expires in JWT_EXPIRES_MINUTES minutes. After JWT_EXPIRES_MINUTES minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """

    exp = datetime.utcnow() + timedelta(minutes=jwt_expires_minutes)

    iat = datetime.utcnow()
    token = {
        # The time that the token was issued at
        "iat": iat,
        # The time the token expires.
        "exp": exp,
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "rb") as f:
        signing_key = f.read()

    logger.info(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return jwt.encode(token, signing_key, algorithm=algorithm)
