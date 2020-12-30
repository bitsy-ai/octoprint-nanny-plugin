from datetime import datetime, timedelta
import ssl
import jwt
import logging
import os
import paho.mqtt.client as mqtt


JWT_EXPIRES_MINUTES = os.environ.get("OCTOPRINT_NANNY_MQTT_JWT_EXPIRES_MINUTES", 60)
GCP_PROJECT_ID = os.environ.get("OCTOPRINT_NANNY_GCP_PROJECT_ID", "print-nanny")
GCP_MQTT_BRIDGE_HOSTNAME = os.environ.get(
    "OCTOPRINT_NANNY_GCP_MQTT_BRIDGE_HOSTNAME", "mqtt.googleapis.com"
)
GCP_MQTT_BRIDGE_PORT = os.environ.get("OCTOPRINT_NANNY_GCP_MQTT_BRIDGE_PORT", 443)
GCP_IOT_DEVICE_REGISTRY = os.environ.get(
    "OCTOPRINT_NANNY_GCP_IOT_DEVICE_REGISTRY", "devices-us-central1-dev"
)
GCP_IOT_DEVICE_REGISTRY_REGION = os.environ.get(
    "OCTOPRINT_NANNY_GCP_IOT_DEVICE_REGISTRY_REGION", "us-central1"
)


logger = logging.getLogger("octoprint.plugins.octoprint_nanny.clients.mqtt")


class MQTTClient:
    def __init__(
        self,
        device_id: str,
        private_key_file: str,
        ca_certs,
        algorithm="RS256",
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
        tls_version=ssl.PROTOCOL_TLSv1_2,
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

        self.client = mqtt.Client(client_id=client_id)

        # register callback functions
        if on_connect:
            self.client.on_connect = on_connect
        if on_disconnect:
            self.client.on_disconnect = on_disconnect
        if on_message:
            self.client.on_message = on_message
        if on_publish:
            self.client.on_publish = on_publish
        if on_subscribe:
            self.client.on_subscribe = on_subscribe
        if on_unsubscribe:
            self.client.on_unsubscribe = on_unsubscribe

        # device receives configuration updates on this topic
        self.mqtt_config_topic = f"/devices/{self.device_id}/config"

        # device receives commands on this topic
        self.mqtt_command_topic = f"/devices/{self.device_id}/commands/#"

        # configure tls
        self.client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
        # With Google Cloud IoT Core, the username field is ignored, and the
        # password field is used to transmit a JWT to authorize the device.
        self.client.username_pw_set(
            username="unused",
            password=create_jwt(project_id, private_key_file, algorithm),
        )

    def connect(self):
        self.client.connect(self.mqtt_bridge_hostname, self.mqtt_bridge_port)

        # subscribe config topic (qos=1 message guaranteed to be transmitted at least once)
        logger.info(
            f"Subscribing device_id={self.device_id} to topic {self.mqtt_config_topic}"
        )
        self.client.subscribe(self.mqtt_config_topic, qos=1)
        # subscribe command topic (qos=2 message delivered exactly once)
        logger.info(
            f"Subscribing device_id={self.device_id} to topic {self.mqtt_command_topic}"
        )
        self.client.subscribe(self.mqtt_command_topic, qos=2)

    def publish(self, topic, payload, retain=False, qos=2):

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
        return self.client.publish(topic, payload, qos=qos, retain=retain)


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

    token = {
        # The time that the token was issued at
        "iat": datetime.utcnow(),
        # The time the token expires.
        "exp": datetime.utcnow() + timedelta(minutes=jwt_expires_minutes),
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "r") as f:
        private_key = f.read()

    logger.info(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return jwt.encode(token, private_key, algorithm=algorithm)
