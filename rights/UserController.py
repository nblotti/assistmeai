import base64
import io
import json
import os
import random
from typing import Annotated, Optional, List

import jwt
import pyotp
import qrcode
from fastapi import APIRouter, Depends, Body, Query, Request
from fastapi import HTTPException
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
from starlette.responses import Response, StreamingResponse

from CustomEncoder import CustomEncoder
from ProviderManager import user_dao_provider, category_dao_provider
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

    groups = get_groups(user_repository, user)
    categories = get_categories(category_repository, groups, user)

    return {"user": user,
            "groups": groups,
            "categories": categories,
            "jwt": create_jwt_token(payload)}


@router_user.post("/login/local")
async def do_login_local(user_repository: user_repository_dep, category_repository: category_repository_dep,
                         request: Request):
    # Read the payload from the request
    payload = await request.json()

    user = payload["info"]["sub"]
    qrcode = payload["info"]["secondFactor"]
    userPassword = payload["info"]["userPassword"]
    payload["info"]["exp"] = "1726398000000"

    code = get_gid_password(user)

    if userPassword != code[1].decode('utf-8'):
        raise HTTPException(401, "user not verified")

    # Generate OTP secret
    otp_secret = random_base32(int(code[0]))

    # Create TOTP object
    generate_qrcode = pyotp.TOTP(otp_secret)

    if not generate_qrcode.verify(qrcode):
        raise HTTPException(401, "user not verified")

    groups = get_groups(user_repository, user)
    categories = get_categories(category_repository, groups, user)

    return {"user": user,
            "groups": groups,
            "categories": categories,
            "jwt": create_jwt_token(payload)}


def random_base32(seed=None):
    if seed is not None:
        random.seed(seed)
    random_bytes = random.randbytes(20)  # 20 bytes for a 160-bit output
    return base64.b32encode(random_bytes).decode('utf-8')


@router_user.post("/generate-qrcode/")
async def generate_qrcode(request: Request):
    payload = await request.json()

    user = payload["info"]["sub"]

    userPassword = payload["info"]["userPassword"]

    code = get_gid_password(user)

    if userPassword != code[1].decode('utf-8'):
        raise HTTPException(401, "user not verified")

    # Generate OTP secret
    otp_secret = random_base32(int(code[0]))

    # Create TOTP object
    totp = pyotp.TOTP(otp_secret)

    # Create provisioning URL for Google Authenticator
    provisioning_url = totp.provisioning_uri(name=user, issuer_name=os.getenv("PROVISIONNING_URL"))

    # Generate QR code
    qr = qrcode.make(provisioning_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router_user.post("/get-qr/")
async def get_qr_endpoint(user: str):
    return get_gid_password(user)


@router_user.get("/validate")
async def validate():
    # for test only
    pass


@router_user.get("/categories")
async def get_all_categories_for_ids(user_repository: user_repository_dep, category_repository: category_repository_dep,
                                     user_ids: Optional[List[int]] = Query(None)):
    results = []
    for cur_id in user_ids:
        results.append(str(cur_id))
    category_ids = user_repository.list_by_group(results)

    category_ids = [result[2] for result in category_ids]
    categories = category_repository.list_by_group_ids(category_ids)
    return categories


@router_user.get("/")
async def get_all_users():
    search_filter = "(objectClass=organizationalPerson)"
    entries = query_ldap_(search_filter, ['cn', 'givenName'])

    cn_list = []
    # Collect the results
    for entry in entries:
        cn_list.append({"cn": entry.cn.value, "givenName": entry.givenName.value})
    return cn_list


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
    category = category_repository.save(new_category["category_name"])
    if not category:
        return Response(status_code=404)

    return json.loads(json.dumps(user_repository.save(new_category["user_id"],
                                                      category[0]), cls=CustomEncoder))


def get_gid_password(user: str):
    try:
        # Ensure all required variables are defined and strings
        if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
            raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

        # Define the search filter
        search_filter = f"(cn={user})"

        # Perform the LDAP query
        entries = query_ldap_(search_filter, ['cn', 'gidNumber', 'userPassword'])

        # Collect the results
        cn_list = [(entry['gidNumber'][0], entry['userPassword'][0]) for entry in entries if
                   'gidNumber' in entry and 'userPassword' in entry]

        # Check if the list is not empty and raise HTTPException
        if not cn_list:
            raise HTTPException(status_code=401, detail="Error while retrieving the user")

        return cn_list[0]


    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def add_qr_to_user(cn: str, code: str):
    try:
        # Connect to the LDAP server
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

        # Define the distinguished name (DN) of the user
        user_dn = f"cn={cn},ou=users,{ldap_base_dn}"

        # Prepare the modification
        modifications = {
            'qrcode': [(MODIFY_REPLACE, [code])]
        }

        # Perform the modification
        if not conn.modify(user_dn, modifications):
            raise ValueError(f"Failed to modify user: {conn.result['description']}")

        # Unbind the connection
        conn.unbind()

        return {"status": "success", "message": "QR code attribute added successfully"}

    except Exception as e:
        print(f"Error occurred: {e}")
        return {"status": "error", "message": str(e)}


def create_jwt_token(login_info):
    payload = {
        'user_id': login_info["info"]["sub"],
        'exp': login_info["info"]["exp"],  # Token will expire in 1 hour
    }
    # Your secret key (guard it with your life!)

    token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
    return token


def query_ldap_(search_filter, search_attributes):
    try:
        # Ensure all are strings
        if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
            raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

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

        entries = []

        entries = conn.entries

        # Make sure to unbind the connection after using it.
        conn.unbind()

        return entries

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_groups(user_repository, user):
    try:
        # Ensure all are strings
        if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
            raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

        search_filter = f"(member=cn={user},ou=users,{ldap_base_dn})"
        entries = query_ldap_(search_filter, ['cn'])
        # Define the search filter

        cn_list = []
        # Collect the results
        for entry in entries:
            cn_list.append(entry.cn.value)
        return cn_list

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_categories(category_repository: category_repository_dep, groups, user):
    # category_ids = [result[2] for result in category_ids]
    categories = category_repository.list_by_group_ids(groups)
    # Create the initial dictionary with user and "MyDocuments"
    initial_entry = (user, 0, "MyDocuments", True)

    # Add the initial dictionary at the beginning of the categories list
    categories.insert(0, initial_entry)

    return categories
