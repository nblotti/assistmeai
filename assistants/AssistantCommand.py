from typing import Optional

from pydantic import BaseModel


# Define the Python class as a Pydantic model

class AssistantCommand(BaseModel):
    id: Optional[str] = None
    command: str
    conversation_id: Optional[str] = ""
