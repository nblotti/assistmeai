from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, Query, Request

from ProviderManager import user_dao_provider, category_dao_provider, user_manager_provider
from document.DocumentCategory import DocumentCategoryCreate, DocumentCategoryByGroupCreate
from document.DocumentCategoryRepository import DocumentCategoryRepository
from rights.User import UserGroupCreate
from rights.UserManager import UserManager
from rights.UserRepository import UserRepository

router_user = APIRouter(
    prefix="/user",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

user_repository_dep = Annotated[UserRepository, Depends(user_dao_provider)]
category_repository_dep = Annotated[DocumentCategoryRepository, Depends(category_dao_provider)]
user_manager_dep = Annotated[UserManager, Depends(user_manager_provider)]


@router_user.post("/login")
async def do_login(user_repository: user_manager_dep, request: Request):
    """
    The use has logged in with SSO. He loads his groups.
    :param category_repository: Dependency injection for the category repository
    :param request: The HTTP request object containing the login details
    :return: A dictionary containing the user's info, LDAP groups, categories, and JWT token
    """
    payload = await request.json()

    return await user_repository.do_login(payload)


@router_user.post("/login/local")
async def do_login_local(user_repository: user_manager_dep,
                         request: Request):
    # Read the payload from the request
    payload = await request.json()

    return await user_repository.do_login_local(payload)


@router_user.post("/generate-qrcode/")
async def generate_qrcode(user_repository: user_manager_dep, request: Request):
    payload = await request.json()

    return await user_repository.generate_qrcode(payload)


@router_user.post("/get-qr/")
async def get_qr_endpoint(user_repository: user_manager_dep, user: str):
    return await user_repository.get_gid_password(user)


@router_user.get("/validate")
async def validate():
    # for test only
    pass


@router_user.get("/")
async def get_all_users(user_repository: user_manager_dep):
    return await user_repository.get_all_users()


@router_user.delete("/{user_id}/")
async def delete(user_repository: user_manager_dep, user_id: str):
    return await user_repository.delete(user_id)


@router_user.put("/categories/")
async def save(user_repository: user_manager_dep,
               new_category: DocumentCategoryCreate) -> UserGroupCreate:
    return await user_repository.save(new_category)


@router_user.get("/categories")
async def get_all_categories_for_ids(user_repository: user_manager_dep,
                                     user_ids: Optional[List[int]] = Query(None)) -> List[
    DocumentCategoryByGroupCreate]:
    return await user_repository.get_all_categories_for_ids(user_ids)
