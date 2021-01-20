from datetime import datetime, timedelta
import ssl
import jwt
import gzip
import logging
import os
import time
import json
import io
import paho.mqtt.client as mqtt

from octoprint_nanny.utils.encoder import NumpyEncoder


JWT_EXPIRES_MINUTES = os.environ.get("OCTOPRINT_NANNY_MQTT_JWT_EXPIRES_MINUTES", 60)
GCP_PROJECT_ID = os.environ.get("OCTOPRINT_NANNY_GCP_PROJECT_ID", "print-nanny")
GCP_MQTT_BRIDGE_HOSTNAME = os.environ.get(
    "OCTOPRINT_NANNY_GCP_MQTT_BRIDGE_HOSTNAME", "mqtt.googleapis.com"
)
GCP_MQTT_BRIDGE_PORT = os.environ.get("OCTOPRINT_NANNY_GCP_MQTT_BRIDGE_PORT", 8883)
GCP_IOT_DEVICE_REGISTRY = os.environ.get(
    "OCTOPRINT_NANNY_GCP_IOT_DEVICE_REGISTRY", "devices-us-central1-prod"
)
GCP_IOT_DEVICE_REGISTRY_REGION = os.environ.get(
    "OCTOPRINT_NANNY_GCP_IOT_DEVICE_REGISTRY_REGION", "us-central1"
)

OCTOPRINT_EVENT_FOLDER = "octoprint-events"
BOUNDING_BOX_EVENT_FOLDER = "bounding-boxes"

logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.mqtt")
device_logger = logging.getLogger(
    "octoprint.plugins.octoprint_nanny.clients.mqtt.device"
)


class MQTTClient:
    def __init__(
        self,
        device_id: str,
        private_key_file: str,
        ca_certs,
        algorithm="RS256",
        remote_control_queue=None,
        mqtt_bridge_hostname=GCP_MQTT_BRIDGE_HOSTNAME,
        mqtt_bridge_port=GCP_MQTT_BRIDGE_PORT,
        on_connect=None,
        on_disconnect=None,
        on_log=None,
        on_message=None,
        on_publish=None,
        on_subscribe=None,
        on_unsubscribe=None,
        project_id=GCP_PROJECT_ID,
        region=GCP_IOT_DEVICE_REGISTRY_REGION,
        registry_id=GCP_IOT_DEVICE_REGISTRY,
        tls_version=ssl.PROTOCOL_TLS,
        message_callbacks=[],  # see message_callback_add() https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#subscribe-unsubscribe
    ):
        self.device_id = device_id
        client_id = f"projects/{project_id}/locations/{region}/registries/{registry_id}/devices/{device_id}"

        self.client_id = client_id
        self.private_key_file = private_key_file
        self.algorithm = algorithm
        self.project_id = project_id
        self.mqtt_bridge_hostname = mqtt_bridge_hostname
        self.mqtt_bridge_port = mqtt_bridge_port
        self.ca_certs = ca_certs
        self.region = region
        self.registry_id = registry_id

        self.tls_version = tls_version
        self.region = region
        self.algorithm = algorithm

        self.remote_control_queue = remote_control_queue

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
        self.mqtt_config_topic = f"/devices/{self.device_id}/config"

        # device receives commands on this topic
        self.mqtt_command_topic = f"/devices/{self.device_id}/commands/#"
        # remote_control app commmands are routed to this subfolder
        self.remote_control_command_topic = (
            f"/devices/{self.device_id}/commands/remote_control"
        )
        # this permits routing on a per-app basis, e.g.
        # /devices/{self.device_id}/commands/my_app_name

        # default telemetry topic
        self.mqtt_default_telemetry_topic = f"/devices/{self.device_id}/events"

        # octoprint event telemetry topic
        self.mqtt_octoprint_event_topic = os.path.join(
            self.mqtt_default_telemetry_topic, OCTOPRINT_EVENT_FOLDER
        )
        # bounding box telemetry topic
        self.mqtt_bounding_boxes_topic = os.path.join(
            self.mqtt_default_telemetry_topic, BOUNDING_BOX_EVENT_FOLDER
        )

        # configure tls
        self.client.tls_set(ca_certs=ca_certs, tls_version=tls_version)

        self.active = False
        self.backoff = 2
        self.max_backoff = 300

    ###
    #   callbacks
    ##

    def _on_message(self, client, userdata, message):
        if message.topic == self.remote_control_command_topic:
            parsed_message = json.loads(message.payload.decode("utf-8"))
            logger.info(
                f"Received remote control command on topic={message.topic} payload={parsed_message}"
            )
            self.remote_control_queue.put_nowait(parsed_message)
            # callback to api to indicate command was received
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
            f"MQTTClient._on_connect called with client={client} userdata={userdata} rc={rc}"
        )

        if rc == 0:
            self.backoff = 2
            logger.info("Device successfully connected to MQTT broker")
            self.client.subscribe(self.mqtt_config_topic, qos=1)
            logger.info(
                f"Subscribing to config updates device_id={self.device_id} to topic {self.mqtt_command_topic}"
            )
            self.client.subscribe(self.mqtt_command_topic, qos=1)
            logger.info(
                f"Subscribing to remote commands device_id={self.device_id} to topic {self.mqtt_command_topic}"
            )
        else:
            logger.error(f"Connection refused by MQTT broker with reason code rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(
            f"Device disconnected from MQTT bridge client={client} userdata={userdata} rc={rc}"
        )
        time.sleep(self.backoff)
        self.backoff = min(self.backoff * 2, self.max_backoff)
        if not self._thread_halt.is_set():

            logger.info(
                "Device attempting to re-authenticate with MQTT broker (JWT probably expired)"
            )
            self.client.username_pw_set(
                username="unused",
                password=create_jwt(
                    self.project_id, self.private_key_file, self.algorithm
                ),
            )
            self.client.reconnect()

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
            topic = self.mqtt_default_telemetry_topic

        return self.client.publish(topic, payload, qos=qos, retain=retain)

    def publish_octoprint_event(self, event, retain=False, qos=1):
        payload = json.dumps(event, cls=NumpyEncoder)
        return self.publish(
            payload, topic=self.mqtt_octoprint_event_topic, retain=retain, qos=qos
        )

    def publish_bounding_boxes(self, event, retain=False, qos=1):
        payload = json.dumps(event, cls=NumpyEncoder).encode("utf-8")
        outfile = io.BytesIO()
        with gzip.GzipFile(fileobj=outfile, mode="w", compresslevel=1) as f:
            f.write(payload)
        payload = outfile.getvalue()
        return self.publish(
            payload, topic=self.mqtt_bounding_boxes_topic, retain=retain, qos=qos
        )

    def run(self, halt):
        self._thread_halt = halt
        self.client.username_pw_set(
            username="unused",
            password=create_jwt(self.project_id, self.private_key_file, self.algorithm),
        )

        self.client.connect(self.mqtt_bridge_hostname, self.mqtt_bridge_port)
        logger.info(f"MQTT client connected to {self.mqtt_bridge_hostname}")
        return self.client.loop_forever()


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
        expires in 20 minutes. After 20 minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """
    _jwt = jwt.JWT()

    exp = jwt.utils.get_int_from_datetime(
        datetime.utcnow() + timedelta(minutes=jwt_expires_minutes)
    )
    iat = jwt.utils.get_int_from_datetime(datetime.utcnow())
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
        signing_key = jwt.jwk_from_pem(f.read())

    logger.info(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return _jwt.encode(token, signing_key, alg=algorithm)
