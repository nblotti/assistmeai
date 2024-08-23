import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from DependencyManager import share_group_document_dao_provider
from sharing.SharedGroup import SharedGroup
from sharing.SharedGroupDocument import SharedGroupDocument
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupUser import SharedGroupUser
from sharing.SharedGroupUserRepository import SharedGroupUserRepository

# Initialize APIRouter
router_shared_group_document = APIRouter(
    prefix="/sharedgroupdocument",
    tags=["sharedgroupdocument"],
    responses={404: {"description": "Not found"}},
)

shared_group_document_repository_dep = Annotated[
    SharedGroupDocumentRepository, Depends(share_group_document_dao_provider.get_dependency)]


@router_shared_group_document.post("/", response_model=SharedGroupDocument)
def create_group(group: SharedGroupDocument, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = shared_group_user_repository.create(group)
    return db_group


@router_shared_group_document.get("/group/{group_id}/", response_model=List[SharedGroupDocument])
def list_group_by_user_id(group_id: str, shared_group_user_repository: shared_group_document_repository_dep):
    return shared_group_user_repository.list_by_group_id(group_id)


@router_shared_group_document.get("/{id}/", response_model=SharedGroupUser)
def read_group(id: int, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Reading group with ID: %s", id)
    return shared_group_user_repository.read(id)


@router_shared_group_document.delete("/{id}/")
def delete_group(id: int, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Deleting group with ID: %s", id)
    db_group = shared_group_user_repository.delete(id)
    logging.debug("Deleted group: %s", db_group)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Item {id} successfully deleted"}
    )