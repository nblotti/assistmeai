from typing import List

from sqlalchemy import and_

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

    def get_conversation_by_id(self, conversation_id:int) -> ConversationCreate:

        results = self.db.query(Conversation, Document).join(Document, Conversation.document_id == Document.id,
                                                             isouter=True).filter(
            Conversation.id == conversation_id).first()

        if len(results) > 2:
            raise Exception("Too many conversation for this ID !")

        conversation = results[0]
        document = results[1]
        document_name = document.name if document else ""
        new_conversation = self.map_to_conversation(conversation, document_name)

        return new_conversation

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_perimeter(self, perimeter) -> List[ConversationCreate]:
        results = (self.db.query(Conversation, Document, Assistant).join(Document,
                                                                         Conversation.document_id == Document.id,
                                                                         isouter=True)
                   .join(Assistant,
                         Assistant.conversation_id == Conversation.id,
                         isouter=True)
                   .filter(Conversation.perimeter == perimeter).order_by(Conversation.id).all())

        conversations = []
        for conversation, document, assistant in results:
            if assistant is not None:
                continue
            document_name = document.name if document else ""

            new_conversation = self.map_to_conversation(conversation, document_name)
            conversations.append(new_conversation)
            # map conversation create

        return conversations

    def delete(self, conversation_id: str):
        affected_rows = self.db.query(Conversation).filter(Conversation.id == conversation_id).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def delete_by_file_id(self, document_id: str):
        affected_rows = self.db.query(Conversation).filter(Conversation.document_id == int(document_id)).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def get_conversation_by_document_id(self, document_id: int, user_id: str):
        results = self.db.query(Conversation, Document).join(Document, Conversation.document_id == Document.id,
                                                             isouter=True).filter(
            and_(
                Conversation.perimeter == user_id,
                Conversation.document_id == document_id)).all()

        conversations = []
        for conversation, document in results:
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
