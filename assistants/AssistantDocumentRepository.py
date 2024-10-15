from typing import List

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.AssistantsDocument import AssistantsDocument, AssistantsDocumentCreate, AssistantsDocumentList


class AssistantDocumentRepository(BaseAlchemyRepository):
    """
    AssistantDocumentRepository is a repository class for managing operations related to
    assistant documents in the database. It extends the BaseAlchemyRepository.

    Methods
    -------
    create(assistant_document: AssistantsDocumentCreate) -> AssistantsDocumentCreate
        Creates a new assistant document in the database.

    delete(assistant_id) -> int
        Deletes an assistant document from the database.

    list_by_assistant_id(assistant_id: str) -> List[AssistantsDocumentList]
        Lists all documents associated with a specific assistant ID.

    map_to_assistant_document_list(assistant_document: AssistantsDocument) -> AssistantsDocumentList
        Maps an AssistantsDocument instance to an AssistantsDocumentList instance.
    """

    def create(self, assistant_document: AssistantsDocumentCreate) -> AssistantsDocumentCreate:
        new_assistant = AssistantsDocument(
            assistant_id=int(assistant_document.assistant_id),
            document_id=int(assistant_document.document_id),
            document_name=assistant_document.document_name,

        )
        self.db.add(new_assistant)
        self.db.commit()
        self.db.refresh(new_assistant)
        assistant_document.id = new_assistant.id
        return assistant_document

    def delete(self, assistant_id) -> int:
        """
        :param assistant_id: The unique identifier of the assistant to be deleted
        :return: The number of rows affected by the delete operation
        """
        affected_rows = self.db.query(AssistantsDocument).filter(AssistantsDocument.id == assistant_id).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def list_by_assistant_id(self, assistant_id: str) -> List[AssistantsDocumentList]:
        """
        :param assistant_id: The unique identifier of the assistant to filter the documents.
        :return: A list of AssistantsDocumentList objects corresponding to the given assistant_id.
        """
        try:
            assistant_id_int = int(assistant_id)
        except ValueError:
            # Handle error or raise an informative exception
            raise ValueError(f"Provided assistant_id '{assistant_id}' cannot be converted to an integer.")

        assistant: List[AssistantsDocument] = self.db.query(AssistantsDocument).filter(
            AssistantsDocument.assistant_id == assistant_id_int).all()

        return [self.map_to_assistant_document_list(doc) for doc in assistant]

    def map_to_assistant_document_list(self, assistant_document: AssistantsDocument) -> AssistantsDocumentList:
        """
        :param assistant_document: AssistantsDocument object to be converted.
        :return: AssistantsDocumentList object containing the mapped values.
        """
        return AssistantsDocumentList(
            id=str(assistant_document.id),
            assistant_id=str(assistant_document.assistant_id),
            document_id=str(assistant_document.document_id),
            document_name=assistant_document.document_name
        )
