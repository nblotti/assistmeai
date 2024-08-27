from typing import Optional

from pydantic import BaseModel
from datetime import date


class SharedGroupUser(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    group_id: str
    user_id: str
    creation_date: date