import json
import logging
import time
from typing import List

import requests
from fastapi import APIRouter
from fastapi.openapi.models import Response
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool, StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import load_config
from tools.tools import get_wikipedia_retreiver

pms_ai = APIRouter(
    prefix="/pms",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

interaction_manager_provider = load_config()

chat = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, verbose=True)


@pms_ai.get("/")
def do_portfolio_command(command):
    start = time.time()

    chat = ChatOpenAI()
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

    run_query_tool = StructuredTool.from_function(
        func=get_strategy_info,
        name="financial_strategy_executor",
        description="Based on a liste of quotes, a starting date and an amout to invest, generates entries.",
        return_direct=True
        # coroutine= ... <- you can specify an async method if desired as well
    )

    tools = [run_query_tool]

    agent = OpenAIFunctionsAgent(
        llm=chat,
        prompt=prompt,
        tools=tools
    )

    agent_executor = AgentExecutor(
        agent=agent,
        verbose=True,
        tools=tools
    )

    return agent_executor.invoke(
        {"input": command},
        return_only_outputs=True,
    )

    end = time.time()

    return Response(status_code=200)


class TickerInfoItem(BaseModel):
    ticker: str


class StrategyDescription(BaseModel):
    ticker_info: List[TickerInfoItem]
    start_date: str
    amount: int


def get_strategy_info(tickers_info_item: StrategyDescription):
    url_entries = "https://portfolio.nblotti.org/simulation/command"
    url_positions = "https://portfolio.nblotti.org/simulation/porfolio"

    payload = {"content": tickers_info_item.dict()}
    response = requests.post(url_entries, json=payload)
    payload = {"content": response.json()}
    response = requests.post(url_positions, json=payload)
    return response.json()
