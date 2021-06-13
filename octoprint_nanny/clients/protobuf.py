import octoprint
import print_nanny_client
from print_nanny_client.protobuf.common_pb2 import (
    OctoprintEnvironment,
    Metadata,
    PrintSession,
)
from print_nanny_client.protobuf.monitoring_pb2 import MonitoringImage


def build_octoprint_environment(plugin_settings) -> OctoprintEnvironment:
    """
    plugin_settings.environment
    {'os': {'id': 'linux', 'platform': 'linux', 'bits': 32}, 'python': {'version': '3.7.3', 'pip': '21.1.2', 'virtualenv': '/home/pi/oprint'}, 'hardware': {'cores': 4, 'freq': 1500.0, 'ram': 3959304192}, 'plugins': {'pi_support': {'model': 'Raspberry Pi 4 Model B Rev 1.1', 'throttle_state': '0x0', 'octopi_version': '0.18.0'}}}

    """

    octoprint_environment = plugin_settings.metadata.octoprint_environment
    return OctoprintEnvironment(
        plugin_version=plugin_settings.metadata.plugin_version,
        client_version=print_nanny_client.__version__,
        python_version=octoprint_environment.get("python", {}).get("version"),
        pip_version=octoprint_environment.get("python", {}).get("pip"),
        octopi_version=octoprint_environment.get("plugins", {})
        .get("pi_support", {})
        .get("octopi_version"),
        virtualenv=octoprint_environment.get("python", {}).get("virtualenv"),
        platform=octoprint_environment.get("os", {}).get("platform"),
        bits=octoprint_environment.get("os", {}).get("bits"),
        cores=octoprint_environment.get("hardware", {}).get("cores"),
        freq=octoprint_environment.get("hardware", {}).get("freq"),
        ram=octoprint_environment.get("hardware", {}).get("ram"),
        pi_model=octoprint_environment.get("plugins", {})
        .get("pi_support", {})
        .get("model"),
        pi_throttle_state=octoprint_environment.get("plugins", {})
        .get("pi_support", {})
        .get("throttle_state"),
        octoprint_version=octoprint.util.version.get_octoprint_version_string(),
    )


def build_metadata(plugin_settings) -> Metadata:
    octoprint_environment = build_octoprint_environment(plugin_settings)

    return Metadata(
        print_session=plugin_settings.print_session_pb,
        user_id=plugin_settings.metadata.user_id,
        octoprint_device_id=plugin_settings.metadata.octoprint_device_id,
        cloudiot_device_id=plugin_settings.metadata.cloudiot_device_id,
        octoprint_environment=octoprint_environment,
    )


def build_monitoring_image(
    image_bytes: bytes, height: int, width: int, plugin_settings
) -> MonitoringImage:

    metadata = build_metadata(plugin_settings)
    return MonitoringImage(
        data=image_bytes, height=height, width=width, metadata=metadata
    )
