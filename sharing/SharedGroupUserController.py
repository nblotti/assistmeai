import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from ProviderManager import shared_group_user_dao_provider
from sharing.SharedGroupUser import SharedGroupUserCreate
from sharing.SharedGroupUserRepository import SharedGroupUserRepository

# Initialize APIRouter
router_shared_group_user = APIRouter(
    prefix="/sharedgroupuser",
    tags=["sharedgroupuser"],
    responses={404: {"description": "Not found"}},
)

shared_group_user_repository_dep = Annotated[
    SharedGroupUserRepository, Depends(shared_group_user_dao_provider)]


@router_shared_group_user.post("/", response_model=SharedGroupUserCreate)
def create_group(group: SharedGroupUserCreate, shared_group_user_repository: shared_group_user_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = shared_group_user_repository.create(group)
    return db_group


@router_shared_group_user.get("/user/{user_id}/", response_model=List[SharedGroupUserCreate])
def read_group(user_id: str, shared_group_user_repository: shared_group_user_repository_dep):
    logging.debug("Reading groups with user_id :: %s", user_id)
    return shared_group_user_repository.list_by_user_id(user_id)


@router_shared_group_user.get("/group/{group_id}/", response_model=List[SharedGroupUserCreate])
def read_group(group_id: int, shared_group_user_repository: shared_group_user_repository_dep):
    logging.debug("Reading groups with group_id :: %s", group_id)
    return shared_group_user_repository.list_by_group_id(group_id)


@router_shared_group_user.delete("/{id}/")
def delete_group(id: int, shared_group_user_repository: shared_group_user_repository_dep):
    logging.debug("Deleting group with ID: %s", id)
    db_group = shared_group_user_repository.delete(id)
    logging.debug("Deleted group: %s", db_group)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Item {id} successfully deleted"}
    )
