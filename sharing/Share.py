from typing import Optional

from pydantic import BaseModel
from datetime import date


class Share(BaseModel):
    id: Optional[int] = None  # Marking 'id' as optional
    group_id: str
    document_id: str
    creation_date: date
