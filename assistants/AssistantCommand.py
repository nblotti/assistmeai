from typing import Optional

from pydantic import BaseModel

DEFAULT_CONVERSATION_ID = ""


# Define the Python class as a Pydantic model

# Define the Python class as a Pydantic model
# pragma: no cover
class AssistantCommand(BaseModel):
    """
    Represents a command given to a virtual assistant.

    This class encapsulates the details of a command including the command itself,
    an optional identifier, and a conversation ID. It is used to structure and
    manage commands issued during interactions with virtual assistants.

    :ivar id: Optional identifier for the command.
    :type id: str, optional
    :ivar command: The actual command issued to the assistant.
    :type command: str
    :ivar conversation_id: Identifier for the conversation, defaults to
        DEFAULT_CONVERSATION_ID if not provided.
    :type conversation_id: str, optional
    """
    id: Optional[str] = None
    command: str
    conversation_id: Optional[str] = DEFAULT_CONVERSATION_ID
