from datetime import date, datetime
from typing import Optional

import pytz
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Date, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SharedGroupUser(Base):
    __tablename__ = 'shared_group_users'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, nullable=False)
    user_id = Column(String, nullable=False)
    creation_date = Column(Date, nullable=False, default=datetime.now(pytz.utc))


class SharedGroupUserCreate(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    group_id: str
    user_id: str
    creation_date: str
