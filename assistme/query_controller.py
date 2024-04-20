import json
import logging
import time

from fastapi import APIRouter

from assistme.query_manager import process_query

router = APIRouter(
    prefix="/query",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)



@router.post("/")
async def do_query(messages: dict):
    start = time.time()

    res = process_query(messages["messages"])

    end = time.time()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("---------------------------------------------------------------------------")
    logging.debug("Elapsed time for global query : {0}".format(end - start))
    logging.debug("---------------------------------------------------------------------------")

    result = '{{"tool":"{0}"}}'.format(res.value)

    return json.loads(result)

