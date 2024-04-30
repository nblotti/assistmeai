from typing import List

from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseChatMessageHistory

from chat.InteractionManager import InteractionManager
from chat.MessageDAO import MessageDAO


class SqlMessageHistory(BaseChatMessageHistory):
    conversation_id: str
    interaction_manager: InteractionManager

    def __init__(self, conversation_id: str, interaction_manager: InteractionManager):
        self.conversation_id = conversation_id
        self.interaction_manager = interaction_manager

    @property
    def messages(self):
        """ Finds all messages that belong to the given conversation_id """
        return self.interaction_manager.get_messages(self.conversation_id)

    def add_message(self, message: BaseMessage):
        """ Creates and stores a new message tied to the given conversation_id  with the provided role and content """
        return self.interaction_manager.save_message(self.conversation_id, message)

    def clear(self):
        pass


def build_document_memory(interaction_manager: InteractionManager, conversation_id):
    return ConversationBufferMemory(
        chat_memory=SqlMessageHistory(
            conversation_id=conversation_id,
            interaction_manager=interaction_manager
        ),
        return_messages=True,
        memory_key="chat_history",
        output_key="result"
    )
