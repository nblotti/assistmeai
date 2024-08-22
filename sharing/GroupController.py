import json
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from CustomEncoder import CustomEncoder
from DependencyManager import group_dao_provider
from sharing.Group import Group
import logging

from sharing.GroupRepository import GroupRepository

# Initialize APIRouter
router_group = APIRouter(
    prefix="/group",
    tags=["groups"],
    responses={404: {"description": "Not found"}},
)

group_repository_dep = Annotated[GroupRepository, Depends(group_dao_provider.get_dependency)]


@router_group.post("/", response_model=Group)
def create_group(group: Group, group_repository: group_repository_dep):
    logging.debug("Creating group: %s", group)
    db_group = group_repository.create_group(group)
    return db_group


@router_group.get("/owner/{owner_id}/",response_model=List[Group])
def list_group_by_owner(owner_id: str, group_repository: group_repository_dep):

    return group_repository.list_groups_by_owner(owner_id)


@router_group.get("/{group_id}/", response_model=Group)
def read_group(group_id: int, group_repository: group_repository_dep):
    logging.debug("Reading group with ID: %s", group_id)
    return group_repository.get_group(group_id)


@router_group.put("/", response_model=Group)
def update_group(group: Group, group_repository: group_repository_dep):
    logging.debug("Updating group with name: %s", group.name)
    db_group = group_repository.update_group(group)
    if db_group is None:
        logging.error("Group not found with ID: %s", group.id)
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@router_group.delete("/{group_id}/")
def delete_group(group_id: int, group_repository: group_repository_dep):
    logging.debug("Deleting group with ID: %s", group_id)
    db_group = group_repository.delete_group(group_id)
    logging.debug("Deleted group: %s", db_group)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Item {group_id} successfully deleted"}
    )

