from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from message.MessageRepository import MessageRepository


class SqlMessageHistory(BaseChatMessageHistory):
    conversation_id: str
    message_repository: MessageRepository

    def __init__(self, conversation_id: str, message_repository: MessageRepository):
        self.conversation_id = conversation_id
        self.message_repository = message_repository

    @property
    def messages(self):
        """ Finds all messages that belong to the given conversation_id """
        messages = self.message_repository.get_all_messages_by_conversation_id(self.conversation_id)
        current_len = len(messages)
        if current_len >= 10:
            messages = messages[current_len-10:]

        return messages

    def add_message(self, message: BaseMessage):
        """ Creates and stores a new message tied to the given conversation_id  with the provided role and content """
        return self.message_repository.save(self.conversation_id, message)

    def clear(self):
        # TODO NBL : not sure that it is required, but to check
        pass


def build_agent_memory(message_repository: MessageRepository, conversation_id):
    return SqlMessageHistory(
        conversation_id=conversation_id,
        message_repository=message_repository,
    )


def build_memory(message_repository: MessageRepository, conversation_id):
    return ConversationBufferMemory(
        chat_memory=SqlMessageHistory(
            conversation_id=conversation_id,
            message_repository=message_repository
        ),
        return_messages=True,
        input_key="query",
        memory_key="chat_history",
        output_key="result"
    )
