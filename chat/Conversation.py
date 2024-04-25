from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Conversation(BaseModel):
    id:  Optional[str] = None
    perimeter: str
    description: Optional[str] = "New conversation"
    pdf_id: Optional[str] = ""
    pdf_name: Optional[str] = ""
    created_on:  Optional[str] = None



    def as_dict(self):
        return {
            "id": self.id,
            "pdf_id": self.pdf_id,
            "created_on":self.created_on,
            "perimeter": self.perimeter
        }
