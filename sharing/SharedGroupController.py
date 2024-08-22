import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from DependencyManager import shared_group_dao_provider
from sharing.SharedGroup import SharedGroup
from sharing.SharedGroupRepository import SharedGroupRepository

# Initialize APIRouter
router_group = APIRouter(
    prefix="/sharedgroup",
    tags=["sharedgroups"],
    responses={404: {"description": "Not found"}},
)

shared_group_repository_dep = Annotated[SharedGroupRepository, Depends(shared_group_dao_provider.get_dependency)]


@router_group.post("/", response_model=SharedGroup)
def create_group(group: SharedGroup, group_repository: shared_group_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = group_repository.create(group)
    return db_group


@router_group.get("/owner/{owner_id}/", response_model=List[SharedGroup])
def list_group_by_owner(owner_id: str, group_repository: shared_group_repository_dep):
    return group_repository.list_by_owner(owner_id)


@router_group.get("/{group_id}/", response_model=SharedGroup)
def read_group(group_id: int, group_repository: shared_group_repository_dep):
    logging.debug("Reading group with ID: %s", group_id)
    return group_repository.read(group_id)


@router_group.put("/", response_model=SharedGroup)
def update_group(group: SharedGroup, group_repository: shared_group_repository_dep):
    logging.debug("Updating group with name: %s", group.name)
    db_group = group_repository.update(group)
    if db_group is None:
        logging.error("Group not found with ID: %s", group.id)
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@router_group.delete("/{group_id}/")
def delete_group(group_id: int, group_repository: shared_group_repository_dep):
    logging.debug("Deleting group with ID: %s", group_id)
    db_group = group_repository.delete(group_id)
    logging.debug("Deleted group: %s", db_group)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Item {group_id} successfully deleted"}
    )
