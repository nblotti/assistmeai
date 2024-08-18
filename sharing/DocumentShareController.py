from typing import Annotated

from fastapi import APIRouter, Depends

from DependencyManager import document_share_dao_provider, document_share_dao_provider
from sharing.DocumentShareRepository import DocumentShareRepository

router_document_share = APIRouter(
    prefix="/documentshare",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)



document_sharerepository_dep = Annotated[DocumentShareRepository, Depends(document_share_dao_provider.get_dependency)]


@router_document_share.post("/")
async def create_share():
    pass


@router_document_share.get("/{group_id}/")
async def get_share():
    pass


@router_document_share.put("/")
async def update_share():
    pass


@router_document_share.delete("/{group_id}/")
async def delete_share():
    pass
