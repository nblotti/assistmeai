from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserGroup(Base):
    __tablename__ = 'user_groups'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)


class UserGroupCreate(BaseModel):
    id: Optional[str] = None  # Marking 'id' as optional
    group_id: str
    category_id: str