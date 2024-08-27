import json
from datetime import datetime, date


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime("%d.%m.%Y")  # Convert datetime/date object to string in "dd.MM.YYYY" format
        return super().default(obj)  # Call the default method for other types
