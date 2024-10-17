from datetime import date, datetime
from typing import Optional

import pytz
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Date, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SharedGroup(Base):
    __tablename__ = 'shared_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    creation_date = Column(Date, nullable=False, default=datetime.now(pytz.utc))


class SharedGroupCreate(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    name: str
    owner: str
    creation_date: str
