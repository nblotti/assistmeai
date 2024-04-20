from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class Message:
    id: int
    conversation_id: str
    document_id: str
    role: str
    content: str
    created_on = datetime

    def __init__(self, id, conversation_id, role, content, created_on, document_id):
        self.id = id
        self.conversation_id = conversation_id
        self.document_id = document_id
        self.role = role
        self.content = content
        self.created_on = created_on

    def as_lc_message(self) -> HumanMessage | AIMessage | SystemMessage:
        if self.role == "human":
            return HumanMessage(content=self.content)
        elif self.role == "ai":
            return AIMessage(content=self.content)
        elif self.role == "system":
            return SystemMessage(content=self.content)
        else:
            raise Exception(f"Unknown message role: {self.role}")
