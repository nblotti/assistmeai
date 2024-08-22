from fastapi import FastAPI
from contextlib import asynccontextmanager

from fastapi.openapi.models import Response

import config  # Ensure import of config module

# Remaining imports...
from starlette.middleware.cors import CORSMiddleware
from datetime import date
from typing import Optional
import logging
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware

from assistants.AssistantsController import router_assistant
from chat.ChatController import chat_ai
from conversation.ConversationController import router_conversation
from document.DocumentsController import router_file
from message.MessageController import router_message
from rights.UserController import router_user
from sharing.SharedGroupController import router_group
from sharing.DocumentShareController import router_document_share
from sharing.SharedGroupUserController import router_shared_group_user

config.set_verbose(True)
# CORS origins allowed
origins = ["http://localhost:4200", "*"]


# Middleware to disable caching
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response


# Middleware for verifying Bearer tokens
class BearerTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.endswith("/login"):
            return await call_next(request)

        authorization: Optional[str] = request.headers.get('Authorization')
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1]
            return await call_next(request)
        else:
            logging.error("Authorization header missing or invalid")
            return Response(content="Authorization header missing or invalid", status_code=401)

    def verify_token(self, token: str) -> bool:
        try:
            decoded_payload = jwt.decode(jwt=token, key=config.jwt_secret_key, algorithms=[config.jwt_algorithm])
            logging.debug("JWT token is valid : decoded payload: %s", decoded_payload)
            return True
        except ExpiredSignatureError:
            logging.error("JWT Token has expired")
            return True
        except InvalidTokenError:
            logging.error("JWT Token is invalid")
            return True


# Async context manager for application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.debug("Lifespan startup")
    config.load_config()  # Ensure config is loaded, including SessionLocal initialization
    yield
    logging.debug("Lifespan shutdown")


# FastAPI application instance
app = FastAPI(lifespan=lifespan)


@app.get("/ping")
async def ping():
    return {"date": date.today()}


# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(NoCacheMiddleware)
#app.add_middleware(BearerTokenMiddleware)

# Register routers
app.include_router(chat_ai)
app.include_router(router_file)
app.include_router(router_conversation)
app.include_router(router_message)
app.include_router(router_user)
app.include_router(router_assistant)
app.include_router(router_group)
app.include_router(router_shared_group_user)
app.include_router(router_document_share)
