from typing import Optional

from pydantic import BaseModel


class AssistantsDocument(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    assistant_id: str
    document_id: str
    document_name: str
