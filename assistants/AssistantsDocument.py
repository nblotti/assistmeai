from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AssistantsDocument(Base):
    __tablename__ = 'assistants_document'

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, index=True)
    document_id = Column(Integer, index=True)
    document_name = Column(String)


class AssistantsDocumentCreate(BaseModel):
    id: Optional[str] = None
    assistant_id: str
    document_id: str
    document_name: str


class AssistantsDocumentList(AssistantsDocumentCreate):
    pass