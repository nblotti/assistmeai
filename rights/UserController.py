import json
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, Body, Query
from starlette.responses import Response

from CustomEncoder import CustomEncoder
from DependencyManager import user_dao_provider, category_dao_provider
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository

router_user = APIRouter(
    prefix="/user",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

user_repository_dep = Annotated[UserRepository, Depends(user_dao_provider.get_dependency)]
category_repository_dep = Annotated[CategoryRepository, Depends(category_dao_provider.get_dependency)]


@router_user.get("/")
async def get_all_categories_for_ids(user_repository: user_repository_dep, category_repository: category_repository_dep,
                                     user_ids: Optional[List[int]] = Query(None)):
    results = []
    for cur_id in user_ids:
        results.append(str(cur_id))
    category_ids = user_repository.list_by_group(results)

    category_ids = [result[2] for result in category_ids]
    categories = category_repository.get_by_ids(category_ids)
    return categories


@router_user.delete("/{user_id}/")
def delete(user_repository: user_repository_dep, user_id: str):
    user_repository.delete_by_id(user_id)
    return Response(status_code=200)


@router_user.delete("/")
async def delete_all(user_repository: user_repository_dep):
    user_repository.delete_all()
    return Response(status_code=200)


@router_user.put("/")
async def save(user_repository: user_repository_dep, category_repository: category_repository_dep,
               new_category=Body(...)):
    category = category_repository.list_by_name(new_category["category_name"])
    if not category:
        return Response(status_code=404)

    return json.loads(json.dumps(user_repository.save(new_category["user_id"],
                                                      category[0]), cls=CustomEncoder))
