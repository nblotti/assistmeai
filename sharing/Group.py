from typing import Optional

from pydantic import BaseModel
from datetime import date


class Group(BaseModel):
    id: Optional[int] = None  # Marking 'id' as optional
    name: str
    owner: str
    creation_date: date