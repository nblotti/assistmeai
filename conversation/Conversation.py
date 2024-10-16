from datetime import datetime
from typing import Optional

import pytz
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True, index=True)
    perimeter = Column(String, nullable=False)
    document_id = Column(Integer, ForeignKey('document.id'), default=0)
    description = Column(String, nullable=False, default="New conversation")
    created_on = Column(String, nullable=False, default=datetime.now(pytz.utc))


class ConversationCreate(BaseModel):
    id: Optional[int] = None
    perimeter: str
    description: Optional[str] = "New conversation"
    pdf_id: Optional[int] = 0
    pdf_name: Optional[str] = ""
    created_on: Optional[str] = None

