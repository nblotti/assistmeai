from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from ProviderManager import assistant_manager_provider, conversation_dao_provider
from assistants.Assistant import AssistantCreate
from assistants.AssistantCommand import AssistantCommand
from assistants.AssistantsManager import AssistantManager
from conversation.Conversation import ConversationCreate
from conversation.ConversationRepository import ConversationRepository

# Constants
ROUTER_PREFIX = "/assistants"
ROUTER_TAGS = ["items"]
NOT_FOUND_RESPONSE = {404: {"description": "Not found"}}

# Router Initialization
router_assistant = APIRouter(prefix=ROUTER_PREFIX, tags=ROUTER_TAGS, responses=NOT_FOUND_RESPONSE)
assistant_manager_dep = Annotated[AssistantManager, Depends(assistant_manager_provider)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider)]


def build_response_content(result):
    """
    Build a response content dictionary from the given result.

    This function constructs a dictionary containing the "result" key from the given
    result dictionary. If the result dictionary contains a "sources" key, it is also
    included in the response content.

    :param result: The result data containing at least the "output" key
    :type result: dict
    :return: The constructed response content
    :rtype: dict
    """
    response_content = {"result": result["output"]}
    if "sources" in result:
        response_content["sources"] = result["sources"]
    return response_content


@router_assistant.post("/command/")
def execute_command(assistant_command: AssistantCommand,
                    assistant_manager: assistant_manager_dep) -> JSONResponse:
    """
    Executes a command using the assistant manager and returns the result as a JSON response.

    :param assistant_command: Contains the conversation ID and the command to be executed.
    :type assistant_command: AssistantCommand
    :param assistant_manager: Dependency that manages the execution of commands.
    :return: Result of the command execution, wrapped in a JSON response.
    :rtype: JSONResponse
    """
    result = assistant_manager.execute_command(assistant_command.conversation_id,
                                               assistant_command.command)
    return JSONResponse(content=build_response_content(result))


@router_assistant.get("/command/")
async def execute_get_command(command: str, conversation_id: str,
                              assistant_manager: assistant_manager_dep, perimeter: str = None):
    """
    This function handles a GET request to execute a command using the assistant manager
    within a specific conversation context.

    :param command: The command string to be executed by the assistant.
    :type command: str
    :param conversation_id: The unique identifier of the conversation in which the command
        is to be executed.
    :type conversation_id: str
    :param assistant_manager: Dependency that manages assistant operations and facilitates
        the execution of commands.
    :type assistant_manager: assistant_manager_dep
    :param perimeter: Optional parameter defining the scope or boundary within which the
        command is to be executed.
    :type perimeter: str
    :return: JSONResponse containing the result of the command execution.
    :rtype: JSONResponse
    """
    result = assistant_manager.execute_command(conversation_id, command)
    return JSONResponse(content=build_response_content(result))


@router_assistant.post("/")
async def create_assistant(assistant: AssistantCreate,
                           assistant_manager: assistant_manager_dep,
                           conversation_repository: conversation_repository_dep):
    """
    This function handles the creation of a new assistant by saving the relevant
    details to the repository and linking it to a newly created conversation.

    :param assistant: An instance of AssistantCreate used to specify the details
        of the new assistant to be created.
    :type assistant: AssistantCreate

    :param assistant_manager: Dependency that manages the assistant's data. It
        provides the functionality to save and manage assistants.
    :type assistant_manager: assistant_manager_dep

    :param conversation_repository: Dependency handling the conversation data. It
        provides the functionality to save and manage conversations.
    :type conversation_repository: conversation_repository_dep

    :return: The newly created assistant with a linked conversation.
    :rtype: Assistant
    """
    conversation = ConversationCreate(
        perimeter=assistant.user_id,
        description=f"Assistant - {assistant.name}",
        pdf_id=0
    )
    new_conversation = conversation_repository.save(conversation)
    assistant.conversation_id = new_conversation.id
    new_assistant = assistant_manager.save(assistant)
    return new_assistant


@router_assistant.put("/")
async def update_assistant(assistant: AssistantCreate,
                           assistant_manager: assistant_manager_dep):
    """
    Updates the information of an existing assistant using the provided
    assistant data and the assistant manager dependency.

    The endpoint for this function is associated with an HTTP PUT request.
    The assistant's new data is sent to the server which then
    utilizes the assistant manager's update method to process the
    new data and apply it to the existing assistant record.

    :param assistant: The new data for the assistant.
    :type assistant: AssistantCreate
    :param assistant_manager: Dependency injected manager for handling assistant updates.
    :return: The updated assistant information.
    :rtype: Same type as the return of assistant_manager.update method
    """
    return assistant_manager.update(assistant)


@router_assistant.get("/{user_id}/")
async def list_assistants(assistant_manager: assistant_manager_dep, user_id: str):
    """
    Fetches the list of assistants associated with a given user ID.
    The function interacts with the assistant manager to retrieve
    all assistant objects tied to the specified user.

    :param assistant_manager: A dependency providing access to the assistant
        manager containing the assistant-related logic and data retrieval methods.
    :param user_id: A string representing the user's unique identifier.
    :return: A list of assistants associated with the specified user ID.
    """
    return assistant_manager.get_all_assistant_by_user_id(user_id)


@router_assistant.delete("/{assistant_id}/")
async def delete_assistant(assistant_manager: assistant_manager_dep, assistant_id: str):
    """
    Deletes an assistant with the specified assistant_id.

    This function is an endpoint configured to handle HTTP DELETE requests.
    It utilizes the provided assistant_manager dependency to find and delete
    an assistant by their unique identifier.

    :param assistant_manager: The dependency manager responsible for assistants.
    :type assistant_manager: assistant_manager_dep
    :param assistant_id: The unique identifier of the assistant to be deleted.
    :type assistant_id: str

    :return: A response indicating the success or failure of the delete operation.
    :rtype: Response
    """
    assistant_manager.delete_by_assistant_id(assistant_id)
