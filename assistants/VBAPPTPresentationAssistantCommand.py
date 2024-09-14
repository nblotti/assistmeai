from typing import Optional

from pydantic import BaseModel


# Define the Python class as a Pydantic model

class VBAPPTPresentationAssistantCommand(BaseModel):
    id: Optional[str] = None
    command: str
    conversation_id: str
    use_documentation: Optional[bool] = False
