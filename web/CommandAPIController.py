import logging
import time

from langchain.chains.llm import LLMChain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI


url: str = "https://positions.nblotti.org/positions/?start_date=2000-01-01"

from fastapi import APIRouter, BackgroundTasks, requests

router_aicommand = APIRouter(
    prefix="/aicommand",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@router_aicommand.get("/command")
async def do_command(messages: dict):
    start = time.time()

    chat = ChatOpenAI()

    prompt = ChatPromptTemplate(
        input_variables=["content"],
        messages=[
            HumanMessagePromptTemplate.from_template("{content}")
        ]

    )
    chain = LLMChain(
        llm=chat,
        prompt=prompt
    )

    result = chain({"content":messages["content"]})
    end = time.time()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("---------------------------------------------------------------------------")
    logging.debug("Elapsed time for global query : {0}".format(end - start))
    logging.debug("---------------------------------------------------------------------------")

    return dict(role="message",
                content=result)
