from typing import List, Sequence

from sqlalchemy import delete, select

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.AssistantsDocument import AssistantsDocument, AssistantsDocumentCreate, AssistantsDocumentList


class AssistantDocumentRepository(BaseAlchemyRepository):

    def create(self, assistant_document: AssistantsDocumentCreate) -> AssistantsDocumentCreate:
        new_assistant = AssistantsDocument(
            assistant_id=int(assistant_document.assistant_id),
            document_id=int(assistant_document.document_id),
            document_name=assistant_document.document_name,
            assistant_document_type=assistant_document.assistant_document_type,
            shared_group_id=int(
                assistant_document.shared_group_id) if assistant_document.shared_group_id is not None else None

        )
        self.db.add(new_assistant)
        self.db.commit()
        self.db.refresh(new_assistant)
        assistant_document.id = new_assistant.id
        return assistant_document

    def delete(self, assistant_id: int):
        stmt = delete(AssistantsDocument).where(AssistantsDocument.id == assistant_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def list_by_assistant_id(self, assistant_id: int) \
            -> List[AssistantsDocumentList]:
        stmt = select(AssistantsDocument).where(AssistantsDocument.assistant_id == assistant_id)

        assistants: Sequence[AssistantsDocument] = self.db.execute(stmt).scalars().all()

        return [self.map_to_assistant_document_list(assistant) for assistant in assistants]

    def map_to_assistant_document_list(self, assistant_document: AssistantsDocument) -> AssistantsDocumentList:
        return AssistantsDocumentList(
            id=str(assistant_document.id),
            assistant_id=str(assistant_document.assistant_id),
            document_id=str(assistant_document.document_id),
            document_name=assistant_document.document_name,
            assistant_document_type=assistant_document.assistant_document_type,
            shared_group_id=str(assistant_document.shared_group_id) if assistant_document.shared_group_id is
                                                                       not None else None

        )
