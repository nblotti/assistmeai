from datetime import date
from typing import Optional

from pydantic import BaseModel


class SharedGroupDocument(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    group_id: str
    document_id: str
    creation_date: date
