import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends

from DependencyManager import share_group_document_dao_provider, document_dao_provider, embeddings_dao_provider
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from sharing.SharedGroupDocument import SharedGroupDocument
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupUser import SharedGroupUser

# Initialize APIRouter
router_shared_group_document = APIRouter(
    prefix="/sharedgroupdocument",
    tags=["sharedgroupdocument"],
    responses={404: {"description": "Not found"}},
)

shared_group_document_repository_dep = Annotated[
    SharedGroupDocumentRepository, Depends(share_group_document_dao_provider.get_dependency)]
document_repository_dep = Annotated[DocumentsRepository, Depends(document_dao_provider.get_dependency)]
embeddings_repository_dep = Annotated[EmbeddingRepository, Depends(embeddings_dao_provider.get_dependency)]


@router_shared_group_document.post("/", response_model=SharedGroupDocument)
def create_group(group: SharedGroupDocument, shared_group_user_repository: shared_group_document_repository_dep,
                 documents_repository: document_repository_dep, embedding_repository: embeddings_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = shared_group_user_repository.create(group)
    return share_file(group, documents_repository, embedding_repository, expand_perimeter=True)


def share_file(share_document_dto: SharedGroupDocument,
               documents_repository: DocumentsRepository,
               embedding_repository: EmbeddingRepository,
               expand_perimeter: bool = True
               ):
    blob_id = share_document_dto.document_id

    document = documents_repository.get_by_id(blob_id)

    name = document[0]
    content = document[1]
    old_perimeter = document[2]

    temp_file = "./" + blob_id + ".document"
    with open(temp_file, "wb") as file_w:
        file_w.write(content)

    documents_repository.delete_embeddings_by_id(blob_id)

    if expand_perimeter:
        new_perimeter = f"{share_document_dto.group_id}  {old_perimeter}"
    else:
        new_perimeter = old_perimeter.replace(share_document_dto.group_id, "")

    embedding_repository.create_embeddings_for_pdf(blob_id, new_perimeter, temp_file, name)
    return share_document_dto


@router_shared_group_document.get("/group/{group_id}/", response_model=List[SharedGroupDocument])
def list_group_by_user_id(group_id: str, shared_group_user_repository: shared_group_document_repository_dep):
    return shared_group_user_repository.list_by_group_id(group_id)


@router_shared_group_document.get("/{id}/", response_model=SharedGroupUser)
def read_group(id: int, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Reading group with ID: %s", id)
    return shared_group_user_repository.read(id)


@router_shared_group_document.delete("/", response_model=SharedGroupDocument)
def delete_group(group: SharedGroupDocument, shared_group_user_repository: shared_group_document_repository_dep,
                 documents_repository: document_repository_dep, embedding_repository: embeddings_repository_dep):
    logging.debug("Deleting group with ID: %s", group.group_id)
    shared_group_user_repository.delete(group.id)
    return share_file(group, documents_repository, embedding_repository, expand_perimeter=False)
