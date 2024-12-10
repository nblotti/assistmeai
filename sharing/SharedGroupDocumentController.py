import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends

from ProviderManager import share_group_document_dao_provider, document_manager_provider, job_repository_provider
from document.Document import DocumentCreate
from document.DocumentManager import DocumentManager
from job.Job import JobCreate, JobStatus, JobType
from job.JobRepository import JobRepository
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
job_repository_provider_dep = Annotated[JobRepository, Depends(job_repository_provider)]


@router_shared_group_document.post("/", response_model=SharedGroupDocumentCreate)
def create_group(group: SharedGroupDocumentCreate,
                 shared_group_document_repository: shared_group_document_repository_dep,
                 job_repository: job_repository_provider_dep,
                 document_manager: document_manager_dep

                 ):
    logging.debug("Creating group: %s", group)
    db_group = shared_group_document_repository.create(group)
    share_file(db_group,
               shared_group_document_repository,
               document_manager,
               job_repository,
               expand_perimeter=True)
    return db_group


def share_file(shared_document: SharedGroupDocumentCreate,
               shared_group_document_repository: SharedGroupDocumentRepository,
               document_manager: document_manager_dep,
               job_repository: job_repository_provider_dep,
               expand_perimeter: bool = True
               ):
    document: DocumentCreate = document_manager.get_stream_by_id(int(shared_document.document_id))

    shared_group_documents: List[SharedGroupDocumentCreate] = shared_group_document_repository.list_by_document_id(
        int(shared_document.group_id))

    old_perimeter: str = "/" + document.perimeter + "/"
    for shared_document in shared_group_documents:
        old_perimeter += " /" + shared_document.group_id + "/"

    if expand_perimeter:
        new_perimeter = f"/{shared_document.group_id}/  {old_perimeter}"
    else:
        new_perimeter = old_perimeter.replace("/" + shared_document.group_id + "/", "")

    job = JobCreate(
        source=shared_document.document_id,
        owner=new_perimeter,
        status=JobStatus.REQUESTED,
        job_type=JobType.SHARE
    )
    job_repository.save(job)


@router_shared_group_document.get("/{id}/", response_model=SharedGroupDocumentCreate)
def read_group(id: int, shared_group_user_repository: shared_group_document_repository_dep):
    logging.debug("Reading group with ID: %s", id)
    return shared_group_user_repository.read(id)


@router_shared_group_document.delete("/{group_id}/")
def delete_group(group_id: str,
                 group: SharedGroupDocumentCreate,
                 shared_group_document_repository: shared_group_document_repository_dep,
                 job_repository: job_repository_provider_dep,
                 document_manager: document_manager_dep):
    logging.debug("Deleting group with ID: %s", group_id)
    group: SharedGroupDocumentCreate = shared_group_document_repository.read(int(group_id))
    result = shared_group_document_repository.delete(int(group_id))
    share_file(group,
               shared_group_document_repository,
               document_manager,
               job_repository,
               expand_perimeter=False)
    return result


@router_shared_group_document.get("/group/{group_id}/", response_model=List[SharedGroupDocumentCreate])
def list_group_by_user_id(group_id: str, shared_group_user_repository: shared_group_document_repository_dep):
    return shared_group_user_repository.list_by_group_id(int(group_id))
