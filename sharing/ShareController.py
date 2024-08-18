from typing import Annotated

from fastapi import APIRouter, Depends

from DependencyManager import share_dao_provider
from sharing.ShareRepository import ShareRepository

router_share = APIRouter(
    prefix="/share",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)



sharerepository_dep = Annotated[ShareRepository, Depends(share_dao_provider.get_dependency)]


@router_share.post("/")
async def create_share():
    pass


@router_share.get("/{group_id}/")
async def get_share():
    pass


@router_share.put("/")
async def update_share():
    pass


@router_share.delete("/{group_id}/")
async def delete_share():
    pass
