
from datetime import date


from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import config
from assistme.command_controller import router_command
from assistme.screen_controller import router_screen
from assistmeai.AIController import router_ai
from pdf.PdfController import router_file
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

app.include_router(router_command)
app.include_router(router_screen)
app.include_router(router_aicommand)
app.include_router(router_ai)
app.include_router(router_file)

@app.get("/ping")
async def ping():
    return date.today()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
