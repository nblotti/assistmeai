
from datetime import date


from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import config
from chat.ChatController import chat_ai
from files.FilesController import router_file
from web.CommandAPIController import router_aicommand

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


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

app.include_router(router_aicommand)
app.include_router(chat_ai)
app.include_router(router_file)

@app.get("/ping")
async def ping():
    return date.today()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
