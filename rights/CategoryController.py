import json
from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException
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


@router_category.get("/{group_id}/")
def get(category_repository: category_repository_dep, group_id: str):
    return json.loads(json.dumps(category_repository.list_by_group_ids(group_id), cls=CustomEncoder))


@router_category.get("/")
def get_categories(group_ids: str, category_repository: category_repository_dep):
    # Split the incoming group_ids string by comma to form a list
    group_id_list = group_ids.split(',')

    try:
        # Convert to integers if needed (assuming group_id is int)
        group_id_list = [int(group_id) for group_id in group_id_list]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id format. Must be integers.")

    # Call the modified method with the list of group_ids
    result = category_repository.list_by_group_ids(group_id_list)

    # Return the results encoded with CustomEncoder, if needed otherwise use default JSON encoding
    return json.loads(json.dumps(result, cls=CustomEncoder))


@router_category.delete("/{category_id}/")
def delete(category_repository: category_repository_dep, user_id: str):
    category_repository.delete_by_id(user_id)
    return Response(status_code=200)


@router_category.delete("/")
async def delete_all(category_repository: category_repository_dep):
    category_repository.delete_all()
    return Response(status_code=200)
