from typing import List, Tuple, Sequence, Optional

from sqlalchemy import and_, select, delete

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.Assistant import Assistant
from conversation.Conversation import Conversation, ConversationCreate
from document.Document import Document


class ConversationRepository(BaseAlchemyRepository):

    # Function to store a message data in SQLite

    def save(self, conversation: ConversationCreate):
        new_conversation = Conversation(
            perimeter=conversation.perimeter,
            document_id=conversation.pdf_id,
            description=conversation.description

        )
        self.db.add(new_conversation)
        self.db.commit()
        self.db.refresh(new_conversation)
        conversation.id = new_conversation.id
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> ConversationCreate:

        stmt = select(Conversation, Document).join(Document, Conversation.document_id == Document.id,
                                                   isouter=True).where(Conversation.id == conversation_id)

        result: Optional[Tuple[Conversation, Document]] = self.db.execute(stmt).first()

        conversation_tuple: Tuple[Conversation, Document] = result

        if conversation_tuple is None:
            raise Exception("Error selecting conversation !")

        conversation: Conversation = conversation_tuple[0]
        document: Document = conversation_tuple[1]
        document_name = document.name if document else ""
        new_conversation = self.map_to_conversation(conversation, document_name)

        return new_conversation

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_perimeter(self, perimeter) -> List[ConversationCreate]:

        stmt = (select(Conversation, Document, Assistant).join(Document,
                                                               Conversation.document_id == Document.id,
                                                               isouter=True)
                .join(Assistant,
                      Assistant.conversation_id == Conversation.id,
                      isouter=True).where(Conversation.perimeter == perimeter))
        results: Sequence[Tuple[Conversation, Document, Assistant]] = [
            (row.Conversation, row.Document, row.Assistant) for row in self.db.execute(stmt).all()
        ]

        conversations = []
        for row in results:

            conversation: Conversation = row[0]
            document: Document = row[1]
            assistant: Assistant = row[2]

            if assistant is not None:
                continue

            document_name = document.name if document else ""

            new_conversation = self.map_to_conversation(conversation, document_name)
            conversations.append(new_conversation)
        # map conversation create

        return conversations

    def delete(self, conversation_id: int):
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def get_conversation_by_document_id(self, document_id: int, user_id: str):
        stmt = select(Conversation, Document).join(Document, Conversation.document_id == Document.id,
                                                   isouter=True).where(
            and_(
                Conversation.perimeter == user_id,
                Conversation.document_id == document_id)
        )

        results: Sequence[Tuple[Conversation, Document]] = [
            (row.Conversation, row.Document) for row in self.db.execute(stmt).all()
        ]

        conversations = []
        for row in results:
            conversation: Conversation = row[0]
            document: Document = row[1]
            document_name = document.name if document else ""
            new_conversation = self.map_to_conversation(conversation, document_name)
            conversations.append(new_conversation)

        return conversations

    def map_to_conversation(self, conversation: Conversation, pdf_name: str) -> ConversationCreate:
        return ConversationCreate(
            id=str(conversation.id),
            perimeter=conversation.perimeter,
            pdf_id=str(conversation.document_id),
            pdf_name=pdf_name,
            description=conversation.description,
            created_on=conversation.created_on.strftime("%d.%m.%Y")
        )
