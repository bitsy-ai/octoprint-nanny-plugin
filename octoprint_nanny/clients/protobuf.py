import octoprint
import print_nanny_client
from print_nanny_client.protobuf.common_pb2 import OctoprintEnvironment, Metadata
from print_nanny_client.protobuf.monitoring_pb2 import MonitoringImage


def build_octoprint_environment(plugin, plugin_settings) -> OctoprintEnvironment:
    """
    plugin_settings.environment - {'state': {'text': 'Offline', 'flags': {'operational': False, 'printing': False, 'cancelling': False, 'pausing': False, 'resuming': False, 'finishing': False, 'closedOrError': True, 'error': False, 'paused': False, 'ready': False, 'sdReady': False}, 'error': ''}, 'job': {'file': {'name': None, 'path': None, 'size': None, 'origin': None, 'date': None}, 'estimatedPrintTime': None, 'lastPrintTime': None, 'filament': {'length': None, 'volume': None}, 'user': None}, 'currentZ': None, 'progress': {'completion': None, 'filepos': None, 'printTime': None, 'printTimeLeft': None, 'printTimeOrigin': None}, 'offsets': {}, 'resends': {'count': 0, 'ratio': 0}}

    """
    return OctoprintEnvironment(
        plugin_version=plugin._plugin_version,
        client_version=print_nanny_client.__version_,
        python_version=plugin_settings.environment.get("python", {}).get("version"),
        pip_version=plugin_settings.environment.get("python", {}).get("pip"),
        octopi_version=plugin_settings.environment.get("plugins", {})
        .get("pi_support", {})
        .get("octopi_version"),
        virtualenv=plugin_settings.environment.get("python", {}).get("virtualenv"),
        platform=plugin_settings.environment.get("os", {}).get("platform"),
        bits=plugin_settings.environment.get("os", {}).get("bits"),
        cores=plugin_settings.environment.get("hardware", {}).get("cores"),
        freq=plugin_settings.environment.get("hardware", {}).get("freq"),
        ram=plugin_settings.environment.get("hardware", {}).get("ram"),
        pi_model=plugin_settings.environment.get("plugins", {})
        .get("pi_support", {})
        .get("model"),
        pi_throttle_state=plugin_settings.environment.get("plugins", {})
        .get("pi_support", {})
        .get("throttle_state"),
        octoprint_version=octoprint.util.version.get_octoprint_version_string(),
    )


def build_metadata(plugin, plugin_settings) -> Metadata:
    octoprint_environment = build_octoprint_environment(plugin, plugin_settings)

    print_session = (
        plugin_settings.print_session.session if plugin_settings.print_session else None
    )
    print_session_id = (
        plugin_settings.print_session.id if plugin_settings.print_session else None
    )
    return Metadata(
        print_session=print_session,
        print_session_id=print_session_id,
        user_id=plugin_settings.user_id,
        octoprint_device_id=plugin_settings.octoprint_device_id,
        cloudiot_device_id=plugin_settings.cloudiot_device_id,
        octoprint_environment=octoprint_environment,
    )


def build_monitoring_image(
    image_bytes: bytes, height: int, width: int, ts: float, plugin, plugin_settings
) -> MonitoringImage:

    metadata = build_metadata(plugin, plugin_settings)
    return MonitoringImage(
        ts=ts, data=image_bytes, height=height, width=width, metadata=metadata
    )
