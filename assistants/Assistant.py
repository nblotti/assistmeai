from typing import Optional

from pydantic import BaseModel


# Define the Python class as a Pydantic model

class Assistant(BaseModel):
    id: Optional[str] = None
    userid: str
    name: str
    conversation_id: Optional[str] = ""
    description: Optional[str] = ""
    gpt_model_number: Optional[str] = "3.5"
