import enum
from datetime import date, datetime
from typing import Optional

import pytz
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Enum, LargeBinary, DateTime
from sqlalchemy.orm import declarative_base, deferred


class Jobstatus(str, enum.Enum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentType(str, enum.Enum):
    SUMMARY = "SUMMARY"
    DOCUMENT = "DOCUMENT"
    ALL = "ALL"


Base = declarative_base()


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_on = Column(DateTime, nullable=True, default=datetime.now(pytz.utc))
    perimeter = Column(String, nullable=False, )
    document = deferred(Column(LargeBinary))  # Use deferred
    owner = Column(String, nullable=False)
    summary_id = Column(Integer, nullable=True, default=0)
    summary_status = Column(Enum(Jobstatus), nullable=True, default=Jobstatus.NONE)
    document_type = Column(Enum(DocumentType), nullable=True, default=DocumentType.DOCUMENT)


class DocumentCreate(BaseModel):
    id: Optional[str] = None
    name: str
    owner: str
    perimeter: str
    document: Optional[bytes]= None
    created_on: Optional[date] = None
    summary_id: Optional[int] = None
    summary_status: Optional[Jobstatus] = Jobstatus.NONE
    document_type: Optional[DocumentType] = DocumentType.DOCUMENT

    class Config:
        use_enum_values = True  # This will use enum values when serializing/deserializing
