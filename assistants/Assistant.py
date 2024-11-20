from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Extract common default values into constants
DEFAULT_DESCRIPTION = ""
DEFAULT_GPT_MODEL_NUMBER = "4o-mini"
DEFAULT_USE_DOCUMENTS = False
DEFAULT_FAVORITE = False


class Assistant(Base):
    """
    Represents an assistant entity.

    The Assistant class is designed to model the properties and attributes of a virtual assistant.
    It captures essential details required for maintaining and managing assistants within the
    application context.

    :ivar id: Identifier for the assistant entity.
    :type id: int
    :ivar user_id: Identifier for the user to whom the assistant belongs.
    :type user_id: str
    :ivar name: The name of the assistant.
    :type name: str
    :ivar conversation_id: Identifier for the conversation associated with the assistant.
    :type conversation_id: int
    :ivar description: A brief description of the assistant.
    :type description: str, optional
    :ivar gpt_model_number: The model number of GPT that the assistant utilizes.
    :type gpt_model_number: str
    :ivar use_documents: Flag indicating whether the assistant uses documents.
    :type use_documents: bool
    :ivar favorite: Flag indicating whether the assistant is marked as a favorite.
    :type favorite: bool
    """
    __tablename__ = 'assistants'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    conversation_id = Column(Integer, nullable=False)
    description = Column(String, nullable=True, default=DEFAULT_DESCRIPTION)
    gpt_model_number = Column(String, nullable=False, default=DEFAULT_GPT_MODEL_NUMBER)
    use_documents = Column(Boolean, nullable=False, default=DEFAULT_USE_DOCUMENTS)
    favorite = Column(Boolean, nullable=False, default=DEFAULT_FAVORITE)


# Define the Python class as a Pydantic model with consistent naming and types
class AssistantCreate(BaseModel):
    """
    Represents the creation request for an Assistant object in the system.

    An AssistantCreate object holds data required to create a new assistant,
    including optional metadata such as description, model number, and user
    preferences like use of documents and favorites.

    :ivar id: Optional unique identifier for the assistant.
    :type id: str, optional
    :ivar user_id: Identifier of the user creating the assistant.
    :type user_id: str
    :ivar name: Name of the assistant.
    :type name: str
    :ivar conversation_id: Optional identifier for an existing conversation.
    :type conversation_id: str, optional
    :ivar description: Optional text describing the assistant's purpose.
    :type description: str, optional
    :ivar gpt_model_number: Optional identifier for the GPT model to be used.
    :type gpt_model_number: str, optional
    :ivar use_documents: Optional flag indicating if documents are used.
    :type use_documents: bool, optional
    :ivar favorite: Optional flag indicating if the assistant is a favorite.
    :type favorite: bool, optional
    """
    id: Optional[str] = None
    user_id: str
    name: str
    conversation_id: Optional[str] = None
    description: Optional[str] = DEFAULT_DESCRIPTION
    gpt_model_number: Optional[str] = DEFAULT_GPT_MODEL_NUMBER
    use_documents: Optional[bool] = DEFAULT_USE_DOCUMENTS
    favorite: Optional[bool] = DEFAULT_FAVORITE
