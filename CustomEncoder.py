import json
from datetime import datetime


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%d.%m.%Y")  # Convert datetime object to string in "dd.MM.YYYY" format
        return json.JSONEncoder.default(self, obj)
