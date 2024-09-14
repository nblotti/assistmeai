from typing import Optional

from pydantic import BaseModel


# Define the Python class as a Pydantic model

class VBAAssistantCommand(BaseModel):
    id: Optional[str] = None
    command: str
    conversation_id: Optional[str] = ""
    use_documentation: Optional[bool] = False
    memory: Optional[bool] = False
