import base64
import io
import os
import random
from typing import List, Optional

import jwt
import pyotp
import qrcode
from fastapi import HTTPException
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
from starlette.responses import StreamingResponse

from document.Document import CategoryDocumentCreate, DocumentCreate
from document.DocumentCategory import DocumentCategoryByGroupCreate, DocumentCategoryCreate
from document.DocumentCategoryRepository import DocumentCategoryRepository
from document.DocumentManager import DocumentManager
from rights.User import UserGroupCreate
from rights.UserRepository import UserRepository


class UserManager:

    def __init__(self, user_repository: UserRepository, category_repository: DocumentCategoryRepository,
                 document_manager: DocumentManager):
        self.user_repository = user_repository
        self.category_repository = category_repository
        self.document_manager = document_manager

    async def do_login(self, payload: dict):

        user = payload["info"]["sub"]

        # on obtient les groupes LDAP de l'utilisateur
        groups = self.get_ldap_groups(user)
        # on obtient les catégories LDAP de l'utilisateur
        categories: List[DocumentCategoryByGroupCreate] = self.get_categories(groups, user)

        return {"user": user,
                "groups": groups,
                "categories": categories,
                "jwt": self.create_jwt_token(payload)}

    async def do_login_local(self, payload: dict):
        # Read the payload from the request

        user = payload["info"]["sub"]
        qrcode = payload["info"]["secondFactor"]
        userPassword = payload["info"]["userPassword"]
        payload["info"]["exp"] = "1726398000000"

        code = self.get_gid_password(user)

        if userPassword != code[1].decode('utf-8'):
            raise HTTPException(401, "user not verified")

        # Generate OTP secret
        otp_secret = self.random_base32(int(code[0]))

        # Create TOTP object
        generate_qrcode = pyotp.TOTP(otp_secret)

        if not generate_qrcode.verify(qrcode):
            raise HTTPException(401, "user not verified")

        groups = self.get_ldap_groups(user)
        categories = self.get_categories(groups, user)

        return {"user": user,
                "groups": groups,
                "categories": categories,
                "jwt": self.create_jwt_token(payload)}

    def random_base32(self, seed=None):
        if seed is not None:
            random.seed(seed)
        random_bytes = random.randbytes(20)  # 20 bytes for a 160-bit output
        return base64.b32encode(random_bytes).decode('utf-8')

    async def generate_qrcode(self, payload: dict):

        user = payload["info"]["sub"]

        userPassword = payload["info"]["userPassword"]

        code = self.get_gid_password(user)

        if userPassword != code[1].decode('utf-8'):
            raise HTTPException(401, "user not verified")

        # Generate OTP secret
        otp_secret = self.random_base32(int(code[0]))

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

    async def get_qr_endpoint(self, user: str):
        return self.get_gid_password(user)

    async def get_all_users(self):
        search_filter = "(objectClass=organizationalPerson)"
        entries = self.query_ldap_(search_filter, ['cn', 'givenName'])

        cn_list = []
        # Collect the results
        for entry in entries:
            cn_list.append({"cn": entry.cn.value, "givenName": entry.givenName.value})
        return cn_list

    def delete(self, user_id: str):
        return self.user_repository.delete_by_id(int(user_id))

    async def save(self, new_category: DocumentCategoryCreate) -> UserGroupCreate:
        category = self.category_repository.save(new_category)

        user = UserGroupCreate(
            category_id=category.id,
            group_id=new_category.user_id

        )
        return self.user_repository.save(user)

    async def get_all_categories_for_ids(self, user_ids: Optional[List[str]]) -> List[DocumentCategoryByGroupCreate]:
        results = []
        for cur_id in user_ids:
            results.append(str(cur_id))
        categories: List[UserGroupCreate] = self.user_repository.list_by_group(results)

        category_ids = [category.category_id for category in categories]
        categories: List[DocumentCategoryByGroupCreate] = self.category_repository.list_by_group_ids(category_ids)

        return categories

    def get_categories(self, groups, user) -> List[DocumentCategoryByGroupCreate]:
        categories: List[DocumentCategoryByGroupCreate] = self.category_repository.list_by_group_ids(groups)

        initial_entry = DocumentCategoryByGroupCreate(
            group_id=user,
            category_id=0,
            category_name="My Documents",
            enabled=True)

        # Add the initial dictionary at the beginning of the categories list
        categories.insert(0, initial_entry)

        return categories

    def get_gid_password(self, user: str):
        try:
            ldap_url = os.getenv("ldap_url")
            ldap_base_dn = os.getenv("ldap_base_dn")
            ldap_password = os.getenv("ldap_password")

            # Ensure all required variables are defined and strings
            if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
                raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

            # Define the search filter
            search_filter = f"(cn={user})"

            # Perform the LDAP query
            entries = self.query_ldap_(search_filter, ['cn', 'gidNumber', 'userPassword'])

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

    def add_qr_to_user(self, cn: str, code: str):
        try:
            ldap_url = os.getenv("ldap_url")
            ldap_base_dn = os.getenv("ldap_base_dn")
            ldap_password = os.getenv("ldap_password")
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

    def create_jwt_token(self, login_info):
        payload = {
            'user_id': login_info["info"]["sub"],
            'exp': login_info["info"]["exp"],  # Token will expire in 1 hour
        }
        # Your secret key (guard it with your life!)
        jwt_secret_key = os.getenv("jwt_secret_key")
        jwt_algorithm = os.getenv("jwt_algorithm")

        token = jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)
        return token

    def query_ldap_(self, search_filter, search_attributes):
        try:
            ldap_url = os.getenv("ldap_url")
            ldap_base_dn = os.getenv("ldap_base_dn")
            ldap_password = os.getenv("ldap_password")

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

    def get_ldap_groups(self, user):
        try:
            # Ensure all are strings
            ldap_url = os.getenv("ldap_url")
            ldap_base_dn = os.getenv("ldap_base_dn")
            ldap_password = os.getenv("ldap_password")
            if not all(isinstance(arg, str) for arg in [ldap_url, ldap_base_dn, ldap_password]):
                raise ValueError("ldap_url, ldap_base_dn, and ldap_password must all be strings.")

            search_filter = f"(member=cn={user},ou=users,{ldap_base_dn})"
            entries = self.query_ldap_(search_filter, ['cn'])
            # Define the search filter

            cn_list = []
            # Collect the results
            for entry in entries:
                cn_list.append(entry.cn.value)
            return cn_list

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    async def list_documents(self, user: str, category_id: int) -> List[CategoryDocumentCreate]:

        groups = self.get_ldap_groups(user)
        categories = self.get_categories(groups, user)
        if category_id not in [category.category_id for category in categories]:
            raise HTTPException(status_code=401, detail="Not authorized")
        else:
            category_name = next(
                (category.category_name for category in categories if category.category_id == category_id), None)

        docs: List[DocumentCreate] = self.document_manager.list_documents(str(category_id))

        category_documents = [CategoryDocumentCreate(
            id=doc.id,
            name=doc.name,
            owner=doc.owner,
            perimeter=doc.perimeter,
            document=doc.document,
            created_on=doc.created_on,  # Corrected typo
            summary_id=doc.summary_id,
            summary_status=doc.summary_status,
            document_type=doc.document_type,
            category_id=str(category_id),
            category_name=category_name) for doc in docs]  # Removed extra comma

        return category_documents
