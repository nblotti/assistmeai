import logging
from datetime import datetime
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from BaseAlchemyRepository import BaseAlchemyRepository
from message.Message import Message


class MessageRepository(BaseAlchemyRepository):

    # Function to store a message data in SQLite
    def save(self, conversation_id, message: BaseMessage):

        new_message = Message(
            conversation_id=int(conversation_id),
            role=message.type,
            content=message.content,
            created_on=datetime.now(),

        )
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        message.id = new_message.id
        return message

    def get_all_messages_by_conversation_id(self, conversation_id) -> list[BaseMessage]:
        messages: List[Message] = self.db.query(Message).filter(
            Message.conversation_id == int(conversation_id)).all()
        return [self.as_lc_message(message) for message in messages]

    def list_messages(self, messages, arguments):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(messages, (arguments,))
        result = cursor.fetchall()
        conn.close()

        returned: list[BaseMessage] = []
        for row in result:
            returned.append(Message(row[0], row[1], row[2], row[3], row[4]).as_lc_message())
        return returned if returned else []

    def delete_by_conversation_id(self, conversation_id):
        affected_rows = self.db.query(Message).filter(Message.conversation_id == int(conversation_id)).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def as_lc_message(self, message: Message) -> HumanMessage | AIMessage | SystemMessage:
        if message.role == "human":
            return HumanMessage(id=message.id, content=message.content)
        elif message.role == "ai":
            return AIMessage(id=message.id, content=message.content)
        elif message.role == "system":
            return SystemMessage(id=message.id, content=message.content)
        else:
            logging.error(message.role)
            raise ValueError(f"Unknown message role: {message.role}")
