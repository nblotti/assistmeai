from datetime import datetime
from typing import Optional

import pytz
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SharedGroupDocument(Base):
    __tablename__ = 'shared_group_document'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, nullable=False)
    document_id = Column(Integer, nullable=False)
    creation_date = Column(Date, nullable=False, default=datetime.now(pytz.utc))


class SharedGroupDocumentCreate(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    group_id: str
    document_id: str
    creation_date: Optional[str] = None
