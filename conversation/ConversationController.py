import json
from typing import Annotated

from fastapi import APIRouter, Query, Depends
from fastapi import Response

from CustomEncoder import CustomEncoder
from ProviderManager import message_dao_provider, conversation_dao_provider, document_manager_provider
from conversation.Conversation import ConversationCreate
from conversation.ConversationRepository import ConversationRepository
from document import DocumentManager
from message.MessageRepository import MessageRepository

router_conversation = APIRouter(
    prefix="/conversation",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

'''
------------------------------------------------------------------------------------------------------------------------

Conversation entry point

------------------------------------------------------------------------------------------------------------------------
'''

message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider)]
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]


@router_conversation.get("/perimeter/{perimeter}/")
async def conversations(conversation_repository: conversation_repository_dep, perimeter: str):
    """
    :param conversation_repository: The repository instance used to retrieve conversation data.
    :param perimeter: The specific perimeter used to filter conversations.
    :return: A JSON object containing conversations filtered by the given perimeter.
    """
    res = conversation_repository.get_conversation_by_perimeter(perimeter)
    return res


@router_conversation.get("/document/{document_id}/")
async def conversations(conversation_repository: conversation_repository_dep, document_id: str,
                        user_id: str = Query(None)):
    """
    :param conversation_repository: A dependency that provides an interface to retrieve conversation data.
    :param document_id: The unique identifier of the document for which the conversations are being retrieved.
    :param user_id: The unique identifier of the user requesting the conversations. This is an optional parameter.
    :return: A JSON object containing the conversations related to the specified document, serialized using CustomEncoder.
    """
    res = conversation_repository.get_conversation_by_document_id(int(document_id), user_id)
    return res


@router_conversation.delete("/{conversation_id}/")
async def conversations(conversation_repository: conversation_repository_dep, conversation_id: str):
    """
    :param conversation_repository: Instance of the conversation repository dependency that handles data operations.
    :param conversation_id: Identifier of the conversation to be deleted.
    :return: HTTP response with status code 200 indicating successful deletion of the conversation.
    """
    conversation_repository.delete(conversation_id)

    return Response(status_code=200)


@router_conversation.post("/")
async def conversation(conversation_repository: conversation_repository_dep,
                       document_manager: document_manager_dep, new_conversation: ConversationCreate):
    """
    :param conversation_repository: The repository dependency to handle conversation persistence.
    :param document_manager: The dependency to handle document management and retrieval.
    :param new_conversation: The new conversation object to be saved.
    :return: The saved conversation object with additional document information if applicable.
    """
    res = conversation_repository.save(new_conversation)

    if res.pdf_id != 0:
        doc = document_manager.get_by_id(res.pdf_id)
        res.pdf_name = doc.name

    return res
