import json
from typing import Annotated, Optional, List

import jwt
from fastapi import APIRouter, Depends, Body, Query, Request
from ldap3 import Server, Connection, ALL, SUBTREE
from starlette.responses import Response

from CustomEncoder import CustomEncoder
from DependencyManager import user_dao_provider, category_dao_provider
from config import jwt_secret_key, jwt_algorithm, ldap_url, ldap_password, ldap_base_dn
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository

router_user = APIRouter(
    prefix="/user",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

user_repository_dep = Annotated[UserRepository, Depends(user_dao_provider.get_dependency)]
category_repository_dep = Annotated[CategoryRepository, Depends(category_dao_provider.get_dependency)]


@router_user.post("/login")
async def do_login(user_repository: user_repository_dep, category_repository: category_repository_dep,
                   request: Request):
    # Read the payload from the request
    payload = await request.json()

    user = payload["info"]["sub"]

    groups = get_groups(user_repository, payload)
    categories = get_categories(category_repository, groups, user)

    return {"user": user,
            "groups": groups,
            "categories": categories,
            "jwt": create_jwt_token(payload)}

@router_user.get("/validate")
async def validate():
    #for test only
    pass

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


def create_jwt_token(login_info):
    payload = {
        'user_id': login_info["info"]["sub"],
        'exp': login_info["info"]["exp"],  # Token will expire in 1 hour
    }
    # Your secret key (guard it with your life!)

    token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
    return token


@router_user.get("/")
async def get_all_users():
    search_filter = "(objectClass=organizationalPerson)"
    return query_ldap_(search_filter)


def query_ldap_(list_users):
    try:
        # Ensure all are strings
        if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
            raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

        # Define the search filter
        search_filter = "(objectClass=organizationalPerson)"
        search_attributes = ['cn']

        # Setup the server and the connection
        server = Server(ldap_url, get_info=ALL)
        conn = Connection(server=server,
                          user=f"cn=admin,{ldap_base_dn}",
                          password=ldap_password,
                          raise_exceptions=True,
                          authentication='SIMPLE')  # Use SIMPLE for simple binding

        # Bind to the server
        if not conn.bind():
            raise Exception(f"Failed to bind to server: {conn.result}")

        # Perform the search
        conn.search(search_base=ldap_base_dn,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=search_attributes)

        cn_list = []

        # Collect the results
        for entry in conn.entries:
            cn_list.append(entry.cn.value)

        # Make sure to unbind the connection after using it.
        conn.unbind()

        return cn_list

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_groups(user_repository, login_info):
    try:
        # Ensure all are strings
        if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
            raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

        search_filter = f"(member=cn={login_info["info"]["sub"]},ou=users,{ldap_base_dn})"
        cn_list = query_ldap_(search_filter)
        # Define the search filter

        return cn_list

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_categories(category_repository: category_repository_dep, groups, user):
    # category_ids = [result[2] for result in category_ids]
    categories = category_repository.list_by_group_ids(groups)
    # Create the initial dictionary with user and "MyDocuments"
    initial_entry = (user, 0,"MyDocuments",True)

    # Add the initial dictionary at the beginning of the categories list
    categories.insert(0, initial_entry)

    return categories
