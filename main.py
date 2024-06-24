from datetime import date

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import config
from chat.ChatController import chat_ai
from conversation.ConversationController import conversation_router
from document.DocumentsController import router_file
from message.MessageController import message_router
from rights.CategoryController import router_category
from rights.UserController import router_user

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, document, tool windows, actions, and settings.


config.load_config()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_ai)
app.include_router(router_file)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(router_user)
app.include_router(router_category)


@app.get("/ping")
async def ping():
    return date.today()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
