import enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AssistantDocumentType(str, enum.Enum):
    """
    Enumeration for assistant document types.

    This enumeration defines various categories for documents that the assistant can handle.
    It categorizes documents into three types: personal documents, shared documents, and category-specific documents.
    This can be used to filter or identify documents based on their category.

    :ivar MY_DOCUMENTS: Represents user's personal documents.
    :type MY_DOCUMENTS: str
    :ivar SHARED_DOCUMENTS: Represents documents shared with the user.
    :type SHARED_DOCUMENTS: str
    :ivar CATEGORY_DOCUMENTS: Represents documents categorized under certain categories.
    :type CATEGORY_DOCUMENTS: str
    """
    MY_DOCUMENTS = "MY_DOCUMENTS"
    SHARED_DOCUMENTS = "SHARED_DOCUMENTS"
    CATEGORY_DOCUMENTS = "CATEGORY_DOCUMENTS"


class AssistantsDocument(Base):
    """
    ORM class that maps to the 'assistants_document' table in the database.

    This class represents the relationship between assistants and documents, including
    various attributes such as document name, type, and shared group ID.

    :ivar id: Unique identifier for each entry in the assistants_document table.
    :type id: int
    :ivar assistant_id: Identifier for the assistant associated with the document.
    :type assistant_id: int
    :ivar document_id: Identifier for the document.
    :type document_id: int
    :ivar document_name: Name of the document.
    :type document_name: str
    :ivar assistant_document_type: Type of the assistant document.
    :type assistant_document_type: AssistantDocumentType
    :ivar shared_group_id: Identifier for the group with which the document is shared.
    :type shared_group_id: int, optional
    """
    __tablename__ = 'assistants_document'

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, index=True)
    document_id = Column(Integer, index=True)
    document_name = Column(String)
    assistant_document_type = Column(Enum(AssistantDocumentType), nullable=True,
                                     default=AssistantDocumentType.MY_DOCUMENTS)
    shared_group_id = Column(Integer, nullable=True, default=None)


class AssistantsDocumentCreate(BaseModel):
    """
    Handles the creation of assistant documents and their associated details.

    This class is used to manage the identification and categorization of documents linked
    to specific assistants. It facilitates the assignment of documents to groups and defines
    their types within the system.

    :ivar id: Unique identifier for the assistant document.
    :type id: Optional[str]
    :ivar assistant_id: Identifier for the assistant associated with the document.
    :type assistant_id: str
    :ivar document_id: Identifier for the document.
    :type document_id: str
    :ivar document_name: Name of the document.
    :type document_name: str
    :ivar assistant_document_type: Type of the assistant document.
    :type assistant_document_type: Optional[AssistantDocumentType]
    :ivar shared_group_id: Identifier of the group with which the document is shared.
    :type shared_group_id: Optional[str]
    """
    id: Optional[str] = None
    assistant_id: str
    document_id: str
    document_name: str
    assistant_document_type: Optional[AssistantDocumentType] = AssistantDocumentType.MY_DOCUMENTS
    shared_group_id: Optional[str] = None


class AssistantsDocumentList(AssistantsDocumentCreate):
    """
    AssistantsDocumentList class is a specialized version of AssistantsDocumentCreate.

    This class extends the functionality of AssistantsDocumentCreate to handle
    the listing of assistant documents. It inherits all the properties and methods
    from its superclass and may include additional attributes or methods specific to
    the listing of documents.

    :ivar attribute1: Description of attribute1.
    :type attribute1: type
    :ivar attribute2: Description of attribute2.
    :type attribute2: type
    """
    pass
