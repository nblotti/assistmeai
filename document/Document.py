from datetime import date
from typing import Optional

from pydantic import BaseModel


class Document(BaseModel):
    id: Optional[str] = None
    name: str
    owner: str
    perimeter: str
    created_on: Optional[date] = None
