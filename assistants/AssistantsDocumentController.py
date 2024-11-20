import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse
from ProviderManager import assistant_document_dao_provider
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsDocument import AssistantsDocumentCreate, AssistantsDocumentList, AssistantDocumentType

# Constants
API_PREFIX = "/assistantsdocument"
API_TAGS = ["assistantsdocument"]
NOT_FOUND_RESPONSE = {404: {"description": "Not found"}}

# Initialize APIRouter
router_assistant_document = APIRouter(
    prefix=API_PREFIX,
    tags=API_TAGS,
    responses=NOT_FOUND_RESPONSE,
)
assistant_document_repository_dep = Annotated[AssistantDocumentRepository, Depends(assistant_document_dao_provider)]


@router_assistant_document.post("/", response_model=AssistantsDocumentCreate)
def create_assistant_document(assistants_document: AssistantsDocumentCreate,
                              assistant_document_repository: assistant_document_repository_dep):
    """
    Creates a new assistant document and stores it in the repository.

    This method logs the creation process and returns the created document.

    :param assistants_document: The assistant document to be created.
    :type assistants_document: AssistantsDocumentCreate
    :param assistant_document_repository: The repository instance used to store the document.
    :type assistant_document_repository: AssistantDocumentRepository
    :return: The created document as stored in the repository.
    :rtype: AssistantsDocumentCreate
    """
    logging.debug("Creating assistant_document: %s", assistants_document)
    db_document = assistant_document_repository.create(assistants_document)
    return db_document


@router_assistant_document.get("/assistant/{assistant_id}/", response_model=List[AssistantsDocumentList])
def list_assistant_documents_by_assistant(assistant_id: int,
                                          assistant_document_repository: assistant_document_repository_dep):
    """
    List documents by assistant ID.

    This function retrieves a list of documents associated with a specific
    assistant identified by their assistant ID. The documents are fetched
    from the provided assistant document repository.

    :param assistant_id: The ID of the assistant whose documents need to be listed.
    :type assistant_id: int
    :param assistant_document_repository: The repository used to query for the assistant's documents.
    :type assistant_document_repository: AssistantDocumentRepository
    :return: A list of documents associated with the given assistant ID.
    :rtype: List[AssistantsDocumentList]
    """
    return assistant_document_repository.list_by_assistant_id(assistant_id)


@router_assistant_document.delete("/{assistant_id}/")
def delete_assistant_document(assistant_id: int, assistant_document_repository: assistant_document_repository_dep):
    """
    Deletes an assistant document based on the provided assistant ID.

    :param assistant_id: The ID of the assistant document to delete
    :param assistant_document_repository: The repository instance responsible
                                          for managing assistant documents
    :return: A JSON response indicating the result of the delete operation
    """
    logging.debug("Deleting assistant_document with ID: %s", assistant_id)
    assistant_document_repository.delete(assistant_id)
    logging.debug("Deleted assistant_document: %s", assistant_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Assistant document {assistant_id} successfully deleted"}
    )
