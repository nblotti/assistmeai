from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Jobstatus(str, Enum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    SUMMARY = "SUMMARY"
    DOCUMENT = "DOCUMENT"


class Document(BaseModel):
    id: Optional[str] = None
    name: str
    owner: str
    perimeter: str
    created_on: Optional[date] = None
    summary_id: Optional[str] = None
    summary_status: Optional[str] = Jobstatus.NONE
    document_type: Optional[DocumentType] = DocumentType.DOCUMENT

    class Config:
        use_enum_values = True  # This will use enum values when serializing/deserializing
