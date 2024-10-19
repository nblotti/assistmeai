import logging
import os
from typing import Annotated, List

from fastapi import APIRouter, Depends

from ProviderManager import share_group_document_dao_provider, document_manager_provider
from document.Document import DocumentCreate
from document.DocumentManager import DocumentManager
from sharing.SharedGroupDocument import SharedGroupDocumentCreate
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository

# Initialize APIRouter
router_shared_group_document = APIRouter(
    prefix="/sharedgroupdocument",
    tags=["sharedgroupdocument"],
    responses={404: {"description": "Not found"}},
)

shared_group_document_repository_dep = Annotated[
    SharedGroupDocumentRepository, Depends(share_group_document_dao_provider)]
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]


@router_shared_group_document.post("/", response_model=SharedGroupDocumentCreate)
def create_group(group: SharedGroupDocumentCreate, shared_group_user_repository: shared_group_document_repository_dep,
                 document_manager: document_manager_dep):
    logging.debug("Creating group: %s", group)
    db_group = shared_group_user_repository.create(group)
    share_file(db_group, document_manager, expand_perimeter=True)

    return db_group


def share_file(group: SharedGroupDocumentCreate,
               document_manager: document_manager_dep,
               expand_perimeter: bool = True
               ):
    document: DocumentCreate = document_manager.get_stream_by_id(int(group.document_id))

    name = document.name
    content = document.document
    old_perimeter = document.perimeter

    temp_file = "./" + group.document_id + ".document"
    with open(temp_file, "wb") as file_w:
        file_w.write(content)

    document_manager.delete_embeddings_by_id(group.document_id)

    if expand_perimeter:
        new_perimeter = f"/{group.group_id}/  {old_perimeter}"
    else:
        new_perimeter = old_perimeter.replace("/"+group.group_id+"/", "")

    document_manager.create_embeddings_for_pdf(group.document_id, new_perimeter, temp_file, name)

    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    



@router_shared_group_document.get("/{id}/", response_model=SharedGroupDocumentCreate)
def read_group(id: int, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Reading group with ID: %s", id)
    return shared_group_user_repository.read(id)


@router_shared_group_document.delete("/{group_id}/")
def delete_group(group_id: str, shared_group_user_repository: shared_group_document_repository_dep,
                 document_manager: document_manager_dep):
    logging.debug("Deleting group with ID: %s", group_id)
    group: SharedGroupDocumentCreate = shared_group_user_repository.read(int(group_id))
    result = shared_group_user_repository.delete(int(group_id))
    share_file(group, document_manager, expand_perimeter=False)
    return result


@router_shared_group_document.get("/group/{group_id}/", response_model=List[SharedGroupDocumentCreate])
def list_group_by_user_id(group_id: str, shared_group_user_repository: shared_group_document_repository_dep):
    return shared_group_user_repository.list_by_group_id(int(group_id))
