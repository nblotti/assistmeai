from datetime import date

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

import config
from assistants.AssistantsController import router_assistant
from chat.ChatController import chat_ai
from conversation.ConversationController import router_conversation
from document.DocumentsController import router_file
from message.MessageController import router_message
from rights.UserController import router_user

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, document, tool windows, actions, and settings.


config.load_config()

app = FastAPI()

origins = ["*"]


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows only the specified origins
    allow_credentials=True,  # Allows cookies to be included in CORS requests
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
app.add_middleware(
    NoCacheMiddleware)

app.include_router(chat_ai)
app.include_router(router_file)
app.include_router(router_conversation)
app.include_router(router_message)
app.include_router(router_user)

app.include_router(router_assistant)


@app.get("/ping")
async def ping():
    return date.today()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
