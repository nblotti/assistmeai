from typing import List, Sequence, Optional

from sqlalchemy import delete, select

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.AssistantsDocument import AssistantsDocument, AssistantsDocumentCreate, AssistantsDocumentList


class AssistantDocumentRepository(BaseAlchemyRepository):
    """
    Repository class for managing assistant documents using SQLAlchemy.

    This class provides methods to create, delete, and list assistant
    documents in a database. It includes utility methods for converting
    between string and integer representations.

    :ivar db: The database session used for executing queries.
    :type db: Session
    """
    @staticmethod
    def convert_to_int(value: Optional[str]) -> Optional[int]:
        """
        Converts a string to an integer if the string is not None, otherwise returns None.

        :param value: The string to be converted to an integer.
        :type value: Optional[str]
        :return: The converted integer if value is not None, otherwise None.
        :rtype: Optional[int]
        """
        return int(value) if value is not None else None

    @staticmethod
    def convert_to_str(value: Optional[int]) -> Optional[str]:
        """
        Convert an optional integer to an optional string.

        This method takes an optional integer value as input and returns its string
        representation if the value is not None. If the value is None, the method
        returns None.

        :param value: The integer value to be converted to a string. It can be None.
        :type value: Optional[int]
        :return: The string representation of the input value or None if the input
                 value is None.
        :rtype: Optional[str]
        """
        return str(value) if value is not None else None

    def create(self, assistant_document: AssistantsDocumentCreate) -> AssistantsDocumentCreate:
        """
        Creates a new assistant document record in the database.

        This method takes an AssistantsDocumentCreate object, converts its properties to
        integer values where necessary, and creates a new AssistantsDocument record in the
        database. The new record is committed to the database and refreshed to ensure it
        contains the latest data. Finally, the method updates the input object with the newly
        generated id and returns it.

        :param assistant_document: The AssistantsDocumentCreate object containing data for
            the new assistant document.
        :type assistant_document: AssistantsDocumentCreate
        :return: The updated AssistantsDocumentCreate object with the new id.
        :rtype: AssistantsDocumentCreate
        """
        new_assistant = AssistantsDocument(
            assistant_id=self.convert_to_int(assistant_document.assistant_id),
            document_id=self.convert_to_int(assistant_document.document_id),
            document_name=assistant_document.document_name,
            assistant_document_type=assistant_document.assistant_document_type,
            shared_group_id=self.convert_to_int(assistant_document.shared_group_id)
        )
        self.db.add(new_assistant)
        self.db.commit()
        self.db.refresh(new_assistant)
        assistant_document.id = new_assistant.id
        return assistant_document

    def delete(self, assistant_id: int):
        """
        Deletes an assistant record from the AssistantsDocument table by the specified assistant_id.

        Deletes the record with the given assistant_id from the database. Commits the
        transaction after execution and returns the number of rows affected.

        :param assistant_id: The unique identifier of the assistant to delete
        :type assistant_id: int
        :return: The number of rows affected by the delete operation
        :rtype: int
        """
        stmt = delete(AssistantsDocument).where(AssistantsDocument.id == assistant_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def list_by_assistant_id(self, assistant_id: int) -> List[AssistantsDocumentList]:
        """
        Retrieves a list of AssistantsDocumentList objects filtered by the provided assistant ID. This
        method queries the database for AssistantsDocument records that match the specified assistant ID,
        maps them to AssistantsDocumentList objects, and returns the list of mapped objects.

        :param assistant_id: ID of the assistant to filter documents by.
        :type assistant_id: int
        :return: List of AssistantsDocumentList objects.
        :rtype: List[AssistantsDocumentList]
        """
        stmt = select(AssistantsDocument).where(AssistantsDocument.assistant_id == assistant_id)

        assistants: Sequence[AssistantsDocument] = self.db.execute(stmt).scalars().all()

        return [self.map_to_assistant_document_list(assistant) for assistant in assistants]

    def map_to_assistant_document_list(self, assistant_document: AssistantsDocument) -> AssistantsDocumentList:
        """
        Map an `AssistantsDocument` instance to an `AssistantsDocumentList` instance.

        This function takes an instance of `AssistantsDocument` and maps its attributes
        to a new instance of `AssistantsDocumentList` with respective type conversions
        where necessary.

        :param assistant_document: The document to be mapped
        :type assistant_document: AssistantsDocument

        :return: The mapped `AssistantsDocumentList`
        :rtype: AssistantsDocumentList
        """
        return AssistantsDocumentList(
            id=self.convert_to_str(assistant_document.id),
            assistant_id=self.convert_to_str(assistant_document.assistant_id),
            document_id=self.convert_to_str(assistant_document.document_id),
            document_name=assistant_document.document_name,
            assistant_document_type=assistant_document.assistant_document_type,
            shared_group_id=self.convert_to_str(assistant_document.shared_group_id)

        )
