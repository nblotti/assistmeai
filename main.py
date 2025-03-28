import os

from dotenv import load_dotenv

if os.getenv("ENVIRONNEMENT") == "PROD":
    load_dotenv("config/.env")
else:
    load_dotenv("devenv/.env")

from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from httpx import Request
from starlette.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

import jwt
from fastapi import FastAPI
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
# Remaining imports...
from starlette.middleware.cors import CORSMiddleware

import config
# Ensure import of config module
from assistants.AssistantsController import router_assistant
from assistants.AssistantsDocumentController import router_assistant_document
from chat.ChatController import chat_ai
from conversation.ConversationController import router_conversation
from document.DocumentsController import router_file
from message.MessageController import router_message
from rights.UserController import router_user

from job.JobController import router_job

config.set_verbose(False)

# CORS origins allowed
origins = [
    "http://localhost:4200",  # Your frontend application
    os.getenv("BASE_URL"),
    # Add other origins as needed
]


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
        if request.url.path.endswith("/login") or request.url.path.endswith("/login/local") \
                or request.url.path.endswith("/generate-qrcode/"):
            return await call_next(request)

        authorization: Optional[str] = request.headers.get('Authorization')
        # logging.error("header list: %s", request.headers.keys())
        if authorization and authorization.startswith("Bearer "):

            token = authorization.split("Bearer ")[1]
            result = self.verify_token(token)
            return await call_next(request)
        else:
            #logging.error("Authorization header missing or invalid")
            # return Response(content="Authorization header missing or invalid", status_code=401)
            return await call_next(request)

    def verify_token(self, token: str) -> bool:
        try:
            jwt_secret_key = os.getenv("jwt_secret_key")
            jwt_algorithm = os.getenv("jwt_algorithm")
            decoded_payload = jwt.decode(jwt=token, key=jwt_secret_key, algorithms=[jwt_algorithm])
            # logging.info("JWT token is valid : decoded payload: %s", decoded_payload)
            return True
        except ExpiredSignatureError:
            #logging.error("JWT Token has expired")
            return True
        except InvalidTokenError:
            #logging.error("JWT Token is invalid")
            return True


# Async context manager for application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.debug("Lifespan startup")
    config.load_config()  # Ensure config is loaded, including SessionLocal initialization
    config.init_db()  # Initialize the database connection after loading config
    yield
    logging.debug("Lifespan shutdown")


# FastAPI application instance
app = FastAPI(lifespan=lifespan)


# Custom error handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extract the error details from the exception
    errors = exc.errors()
    for error in errors:
        if error['type'] == 'missing':
            field_loc = " -> ".join(error['loc'])
            logger.error(f"Error: Missing required field at location: {field_loc}")
            logger.error(f"Message: {error['msg']}")
            if error.get('input') is None:
                logger.error("Input: None")

    # Return a JSON response with the error details
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )


@app.get("/ping")
async def ping():
    return {"date": date.today()}


# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],  # Explicitly allow Authorization header
)

# Custom middleware
app.add_middleware(NoCacheMiddleware)
app.add_middleware(BearerTokenMiddleware)


# Register routers
app.include_router(chat_ai)
app.include_router(router_file)
app.include_router(router_conversation)
app.include_router(router_message)
app.include_router(router_user)
app.include_router(router_assistant)


app.include_router(router_assistant_document)

app.include_router(router_job)
