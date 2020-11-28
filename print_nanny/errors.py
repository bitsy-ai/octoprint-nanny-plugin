import werkzeug


class SnapshotHTTPException(werkzeug.exceptions.HTTPException):
    code = 500
    description = "Failed to get webcam snapshot. Please check URL configured in Octoprint Settings > Webcam & Timelapse > Snapshot URl."


class WebcamSettingsHTTPException(werkzeug.exceptions.HTTPException):
    code = 500
    description = "Failed to get webcam snapshot. Please check URL configured in Octoprint Settings > Webcam & Timelapse > Snapshot URl."
