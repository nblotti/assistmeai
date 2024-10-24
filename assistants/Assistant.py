from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Assistant(Base):
    __tablename__ = 'assistants'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    conversation_id = Column(Integer, nullable=False)
    description = Column(String, nullable=True, default="")
    gpt_model_number = Column(String, nullable=False, default="4o-mini")
    use_documents = Column(Boolean, nullable=False, default=False)
    favorite = Column(Boolean, nullable=False, default=False)


# Define the Python class as a Pydantic model

class AssistantCreate(BaseModel):
    id: Optional[str] = None
    userid: str
    name: str
    conversation_id: Optional[str] = ""
    description: Optional[str] = ""
    gpt_model_number: Optional[str] = "4o-mini"
    use_documents: Optional[bool] = "false"
    favorite: Optional[bool] = "false"
