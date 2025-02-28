import os
import tempfile
from typing import Annotated, Iterable

from fastapi import APIRouter, Query, Depends, Form, UploadFile, File
from starlette.responses import JSONResponse

from ProviderManager import conversation_dao_provider, document_manager_provider, chat_manager_provider
from chat.ChatManager import ChatManager
from conversation.ConversationRepository import ConversationRepository
from document.DocumentManager import DocumentManager

chat_ai = APIRouter(
    prefix="/chat",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)
'''
------------------------------------------------------------------------------------------------------------------------

Command entry point

------------------------------------------------------------------------------------------------------------------------
'''

chat_manager_dep = Annotated[ChatManager, Depends(chat_manager_provider)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider)]
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]


def format_docs(docs):
    return [doc.metadata for doc in docs]


@chat_ai.get("/command/")
def message(chat_manager: chat_manager_dep,
            command: str, conversation_id: str, perimeter: str = Query(None)):
    result = chat_manager.message(command, conversation_id, perimeter)
    return JSONResponse(content=build_response_content(result))




@chat_ai.post("/voicecommand/")
async def upload_voice_command(
        chat_manager: chat_manager_dep,
        conversation_id: str = Form(...),
        perimeter: str =Form(...),
        file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    result = chat_manager.execute_voice_command(conversation_id, perimeter, tmp_path)
    return JSONResponse(content=build_response_content(result))


def build_response_content(result):
    response_content = {}
    response_content["result"] = result.get("answer")

    if "question" in result:
        response_content["question"] = result.get("question")

    if "context" in result and isinstance(result.get("context"), Iterable):
        try:
            sources = [doc.metadata for doc in result["context"]]
            response_content["sources"] = sources
        except AttributeError:
            pass  # handle the error as per your requirements

    return response_content
