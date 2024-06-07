import time
from fastapi import APIRouter
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from config import load_config
from pms.tools import quarterly_dollar_average_strategy, set_display

pms_ai = APIRouter(
    prefix="/pms",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

interaction_manager_provider = load_config()

chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)


@pms_ai.get("/")
def do_portfolio_command(command):

    ai_chat = ChatOpenAI()
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

    tools = [quarterly_dollar_average_strategy, set_display]

    agent = OpenAIFunctionsAgent(
        llm=ai_chat,
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
