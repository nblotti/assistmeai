import json
from typing import Annotated

from fastapi import APIRouter, Depends, Body
from starlette.responses import Response

from CustomEncoder import CustomEncoder
from DependencyManager import category_dao_provider
from rights.CategoryRepository import CategoryRepository

router_category = APIRouter(
    prefix="/category",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

category_repository_dep = Annotated[CategoryRepository, Depends(category_dao_provider.get_dependency)]


@router_category.post("/")
async def save_category(category_repository: category_repository_dep, category=Body(...)):
    category = category_repository.save(category["name"])
    return category


@router_category.get("/{category_id}/")
def get(category_repository: category_repository_dep, user_id: str):
    return json.loads(json.dumps(category_repository.get_by_id(user_id), cls=CustomEncoder))


@router_category.delete("/{category_id}/")
def delete(category_repository: category_repository_dep, user_id: str):
    category_repository.delete_by_id(user_id)
    return Response(status_code=200)


@router_category.delete("/")
async def delete_all(category_repository: category_repository_dep):
    category_repository.delete_all()
    return Response(status_code=200)
