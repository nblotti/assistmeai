import logging
from datetime import datetime
from typing import Sequence

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy import select, delete

from BaseAlchemyRepository import BaseAlchemyRepository
from message.Message import Message


class MessageRepository(BaseAlchemyRepository):

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

        stmt = select(Message).where(Message.conversation_id == int(conversation_id)).order_by(Message.id.asc())
        messages: Sequence[Message] = self.db.execute(stmt).scalars().all()

        return [self.as_lc_message(message) for message in messages]

    def delete_by_conversation_id(self, conversation_id):
        stmt = delete(Message).where(Message.conversation_id == int(conversation_id))
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

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
