from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DocumentCategory(Base):
    __tablename__ = 'document_category'

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)


class DocumentCategoryCreate(BaseModel):
    id: Optional[str] = None
    name: str


class DocumentCategoryByGroup(Base):
    __tablename__ = 'category_by_group'

    group_id = Column(String, nullable=False, primary_key=True)
    category_id = Column(Integer, nullable=False, primary_key=True)
    category_name = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)


class DocumentCategoryByGroupCreate(BaseModel):
    group_id: Optional[str] = None
    category_id: int
    category_name: str
    enabled: Optional[bool] = True
    is_admin: Optional[bool] = False
