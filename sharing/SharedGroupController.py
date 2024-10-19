import logging
import os
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from ProviderManager import shared_group_dao_provider, document_manager_provider, share_group_document_dao_provider
from document.Document import DocumentCreate
from document.DocumentManager import DocumentManager
from sharing.SharedGroup import SharedGroupCreate
from sharing.SharedGroupDocument import SharedGroupDocumentCreate
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupRepository import SharedGroupRepository

# Initialize APIRouter
router_group = APIRouter(
    prefix="/sharedgroup",
    tags=["sharedgroups"],
    responses={404: {"description": "Not found"}},
)

shared_group_repository_dep = Annotated[SharedGroupRepository, Depends(shared_group_dao_provider)]
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]
shared_group_document_repository_dep = Annotated[
    SharedGroupDocumentRepository, Depends(share_group_document_dao_provider)]


@router_group.post("/", response_model=SharedGroupCreate)
def create_group(group: SharedGroupCreate, group_repository: shared_group_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = group_repository.create(group)
    return db_group


@router_group.get("/owner/{owner_id}/", response_model=List[SharedGroupCreate])
def list_group_by_owner(owner_id: str, group_repository: shared_group_repository_dep):
    return group_repository.list_by_owner(owner_id)


@router_group.get("/{group_id}/", response_model=SharedGroupCreate)
def read_group(group_id: int, group_repository: shared_group_repository_dep):
    logging.debug("Reading group with ID: %s", group_id)
    return group_repository.read(group_id)


@router_group.get("/group/user/{user_id}/", response_model=List[SharedGroupCreate])
def list_group_by_user_id(group_id: str, shared_group_repository: shared_group_repository_dep):
    return shared_group_repository.list_groups_by_user_id(group_id)


@router_group.put("/", response_model=SharedGroupCreate)
def update_group(group: SharedGroupCreate, group_repository: shared_group_repository_dep):
    logging.debug("Updating group with name: %s", group.name)
    db_group = group_repository.update(group)
    if db_group is None:
        logging.error("Group not found with ID: %s", group.id)
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


def unshare_file(group: SharedGroupCreate,
                 document_manager: document_manager_dep,
                 shared_group_document_repository: shared_group_document_repository_dep,
                 ):
    documents: List[SharedGroupDocumentCreate] = shared_group_document_repository.list_by_group_id(int(group.id))

    for doc in documents:
        document_manager.delete_embeddings_by_id(doc.document_id)
        document: DocumentCreate = document_manager.get_stream_by_id(int(doc.document_id))

        name = document.name
        content = document.document
        old_perimeter = document.perimeter

        temp_file = "./" + doc.document_id + ".document"
        with open(temp_file, "wb") as file_w:
            file_w.write(content)

        new_perimeter = old_perimeter.replace("/" + group.id + "/", "")

        document_manager.create_embeddings_for_pdf(doc.document_id, new_perimeter, temp_file, name)

        if os.path.exists(temp_file):
            os.remove(temp_file)


@router_group.delete("/{group_id}/")
def delete_group(group_id: int, group_repository: shared_group_repository_dep,
                 document_manager: document_manager_dep,
                 shared_group_document_repository: shared_group_document_repository_dep):
    logging.debug("Deleting group with ID: %s", group_id)
    shared_group: SharedGroupCreate = group_repository.read(group_id)

    unshare_file(shared_group, document_manager, shared_group_document_repository)
    group_repository.delete(group_id)
    logging.debug("Deleted group: %s", shared_group.id)
