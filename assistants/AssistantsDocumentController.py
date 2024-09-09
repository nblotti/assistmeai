import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from DependencyManager import assistant_document_dao_provider
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsDocument import AssistantsDocument

# Initialize APIRouter
router_assistant_document = APIRouter(
    prefix="/assistantsdocument",
    tags=["assistantsdocument"],
    responses={404: {"description": "Not found"}},
)

assistant_document_repository_dep = Annotated[AssistantDocumentRepository,
Depends(assistant_document_dao_provider.get_dependency)]


@router_assistant_document.post("/", response_model=AssistantsDocument)
def create_group(assistants_document: AssistantsDocument,
                 assistant_document_repository: assistant_document_repository_dep):
    logging.debug("Creating assistant_document: %s", assistants_document)
    db_group = assistant_document_repository.create(assistants_document)
    return db_group


@router_assistant_document.get("/assistant/{assistant_id}/", response_model=List[AssistantsDocument])
def list_group_by_owner(assistant_id: str, assistant_document_repository: assistant_document_repository_dep):
    return assistant_document_repository.list_by_assistant_id(assistant_id)


@router_assistant_document.delete("/{assistant_id}/")
def delete_group(assistant_id: int, assistant_document_repository: assistant_document_repository_dep):
    logging.debug("Deleting assistant_document with ID: %s", assistant_id)
    assistant_document_repository.delete(assistant_id)
    logging.debug("Deleted assistant_document: %s", assistant_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Item {assistant_id} successfully deleted"}
    )
