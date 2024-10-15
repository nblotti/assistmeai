from typing import List

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.AssistantsDocument import AssistantsDocument, AssistantsDocumentCreate, AssistantsDocumentList


class AssistantDocumentRepository(BaseAlchemyRepository):

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
        return self.db.query(AssistantsDocument).delete(AssistantsDocument.id == assistant_id)

    def list_by_assistant_id(self, assistant_id: str) -> List[AssistantsDocumentList]:
        assistant: List[AssistantsDocument] = self.db.query(AssistantsDocument).filter(
            AssistantsDocument.assistant_id == int(assistant_id)).all()

        return [self.map_to_assistant_document_list(doc) for doc in assistant]

    def map_to_assistant_document_list(self, assistant_document: AssistantsDocument) -> AssistantsDocumentList:
        return AssistantsDocumentList(
            id=str(assistant_document.id),
            assistant_id=str(assistant_document.assistant_id),
            document_id=str(assistant_document.document_id),
            document_name=assistant_document.document_name
        )
