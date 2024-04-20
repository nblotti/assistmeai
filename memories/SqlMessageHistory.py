from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseChatMessageHistory

from memories.Message import Message
from memories.MessageDAO import MessageDAO


class SqlMessageHistory(BaseChatMessageHistory, BaseModel):
    conversation_id: str
    document_id: str

    @property
    def messages(self):
        """
           Finds all messages that belong to the given conversation_id

           """
        cur_messages = MessageDAO().get_all_messages_by_conversation_id_and_document_id(self.conversation_id,
                                                                                        self.document_id)

        return cur_messages

    def add_message(self, message: BaseMessage):
        """
           Creates and stores a new message tied to the given conversation_id
               with the provided role and content
           """
        return MessageDAO().save(self.conversation_id, self.document_id, message)

    def clear(self):
        return MessageDAO().delete_documents_by_conversation_id_and_document_id(self.conversation_id, self.document_id)


def build_memory(conversation_id, document_id):
    return ConversationBufferMemory(
        chat_memory=SqlMessageHistory(
            conversation_id=conversation_id,
            document_id=document_id
        ),
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )
