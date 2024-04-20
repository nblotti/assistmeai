import json
import logging
import time





from fastapi import APIRouter, BackgroundTasks, requests

from assistme.screen_manager import process_screen

router_screen = APIRouter(
    prefix="/screen",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@router_screen.post("/")
async def do_command(messages: dict):
    start = time.time()

    res = process_screen(messages["messages"])

    end = time.time()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("---------------------------------------------------------------------------")
    logging.debug("Elapsed time for global query : {0}".format(end - start))
    logging.debug("---------------------------------------------------------------------------")

    return dict(role="message",
         content=res)

