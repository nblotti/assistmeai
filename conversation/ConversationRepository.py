from typing import List

from sqlalchemy import and_

from BaseAlchemyRepository import BaseAlchemyRepository
from conversation.Conversation import Conversation, ConversationCreate
from document.Document import Document


class ConversationRepository(BaseAlchemyRepository):
    GET_CONVERSATION_BY_PERIMETER_QUERY = """SELECT c.id, c.perimeter,c.description, c.document_id,COALESCE(p.name, '') 
    AS document_name,c.created_on FROM conversation c 
    LEFT JOIN document p ON c.document_id = p.id 
    LEFT JOIN assistants a ON a.conversation_id::TEXT = c.id::TEXT 
    WHERE c.perimeter = %s AND a.conversation_id IS NULL;"""

    GET_CONVERSATION_BY_ID_QUERY = """SELECT c.id,c.perimeter, c.description, c.document_id, 
    COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
    left outer join  document p on c.document_id = p.id where c.id=%s"""

    GET_CONVERSATION_BY_FILE_ID_QUERY = """SELECT c.id,c.perimeter, c.description, c.document_id, 
      COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
      left outer join  document p on c.document_id = p.id where c.document_id=%s and c.perimeter=%s
      order by c.created_on DESC"""

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

    def get_conversation_by_id(self, conversation_id) -> ConversationCreate:

        results = (self.db.query(Document, Conversation).filter(Conversation.id == conversation_id)
                   .join(Conversation, Document.id == Conversation.document_id, isouter=True).all())

        for document, conversation in results:
            document_name = document.name if document else ""

            # map conversation create

        return None

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_perimeter(self, perimeter) -> List[ConversationCreate]:
        results = (self.db.query(Conversation, Document).join(Document,
                                                              Conversation.document_id == Document.id,
                                                              isouter=True)
                   .filter(Conversation.perimeter == perimeter).all())

        conversations = []
        for conversation, document in results:
            document_name = document.name if document else ""
            conversations.append(ConversationCreate(
                id=str(conversation.id),
                perimeter=conversation.perimeter,
                document_id=str(conversation.document_id),
                pdf_name=document_name,
                description=conversation.description,
                created_on=conversation.created_on.strftime("%d.%m.%Y")
            ))
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

    def get_conversation_by_document_id(self, document_id, user_id):
        results = (self.db.query(Document, Conversation).filter(
            and_(Conversation.id == document_id,
                 Conversation.perimeter == user_id))
                   .join(Conversation, Document.id == Conversation.document_id, isouter=True).all())

        for document, conversation in results:
            document_name = document.name if document else ""

            # map conversation create

        return None
