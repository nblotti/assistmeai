import enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AssistantDocumentType(str, enum.Enum):
    MY_DOCUMENTS = "MY_DOCUMENTS"
    SHARED_DOCUMENTS = "SHARED_DOCUMENTS"


class AssistantsDocument(Base):
    __tablename__ = 'assistants_document'

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, index=True)
    document_id = Column(Integer, index=True)
    document_name = Column(String)
    assistant_document_type = Column(Enum(AssistantDocumentType), nullable=True,
                                     default=AssistantDocumentType.MY_DOCUMENTS)
    shared_group_id = Column(Integer, nullable=True, default=None)


class AssistantsDocumentCreate(BaseModel):
    id: Optional[str] = None
    assistant_id: str
    document_id: str
    document_name: str
    assistant_document_type: Optional[AssistantDocumentType] = AssistantDocumentType.MY_DOCUMENTS
    shared_group_id: Optional[str] = None


class AssistantsDocumentList(AssistantsDocumentCreate):
    pass
