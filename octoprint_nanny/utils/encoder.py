import json
from enum import Enum
import numpy as np
import datetime
from io import BytesIO
import base64
import PIL


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, BytesIO):
            obj.seek(0)
            obj = obj.read()
            return base64.b64encode(obj).decode()
        elif isinstance(obj, bytes):
            return obj.decode()
        elif isinstance(obj, PIL.Image.Image):
            buffered = BytesIO()
            obj.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode()
        elif isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)
