import json
import time
from enum import Enum
from os import getenv
from sqlite3 import Date

from langchain_openai import OpenAI
from ollama import Client
import logging

from config import use_model, model_lama, ai_request_timeout

logger = logging.getLogger(__name__)
client_open_ai = OpenAI(timeout=ai_request_timeout)
client_lama = Client(host='http://192.168.1.5:32141')


class ProcessType:

    def __init__(self, name: str, url: str, uuid: int = round(time.time())):
        self.name = name
        self.url = url
        self._uuid = uuid

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid


QUERY = ProcessType('query', 'https://assistmeai.nblotti.org/query/')
CLEAR = ProcessType('clear', 'https://assistmeai.nblotti.org/query/clear')
PORTFOLIO = ProcessType('pms', 'https://assistmeai.nblotti.org/command/portfolio')
PRODUCT = ProcessType('product', 'https://assistmeai.nblotti.org/product')
SCREEN = ProcessType('screen', 'https://assistmeai.nblotti.org/screen/')
ERROR = ProcessType('error', '')

types = [QUERY, CLEAR, PORTFOLIO, PRODUCT, SCREEN, ERROR]


def process_command(messages):
    return get_ai_state(messages)


def get_ai_state(messages):
    start = time.time()
    current_message = messages[len(messages) - 1]
    command_messages = [{
        "role": "system",
        "name": "assistant",
        "content": "You are an helpful assistant and your job is to detect what tool to use from the list of tools and"
                   'return it in  the following JSON structure {"tool":"tool";"variable_key":"variable_key"}'
    },
        {
            "role": "system",
            "name": "assistant",
            "content": "If the query is empty or you don't understand the question, return 'error' as a tool"
        },
        {
            "role": "system",
            "name": "assistant",
            "content": "First tool is named 'pms'. It is a tool to manage everything that is related to portfolio. "
                       "The tool is able to create a new portfolio, generate entries, positions,calculate returns, "
                       "compare portfolios or benchmark"
        },
        {
            "role": "system",
            "name": "assistant",
            "content": "Second tool is named 'product'. It is a tool used to get information related to structured "
                       "products. It can read termsheets and give informations about the product characteristics, "
                       "such as striking price, TER,underlyings, ISIN, emitter. "
        },

        {
            "role": "system",
            "name": "assistant",
            "content": "Third tool is named 'screen'. It is a tool used to adapt the user interface. It let a user "
                       "resize all part of the screen"
                       "add /remove component, "
        },
        {
            "role": "system",
            "name": "assistant",
            "content": "return the name of the tool the user should use. If no tool seems to be adapted and no error "
                       "was detected, return 'query'"
        },
        {
            "role": "system",
            "name": "assistant",
            "content": "generate a UUID for variable_key"
        },
        current_message

    ]
    return_type = ERROR
    try:
        if use_model is not model_lama:
            completion = client_open_ai.chat.completions.create(
                model=use_model,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=command_messages

            )

            last_message = json.loads(completion.choices[0].message.content)



        else:
            response = client_lama.chat(model=use_model,
                                        format="json",
                                        messages=command_messages)

            last_message = json.loads(response["message"]["content"])

        for obj in types:
            if obj.name == last_message["tool"]:
                obj.uuid = last_message["variable_key"]
                return_type = obj

        logger.debug(last_message["reason"])
        end = time.time()
        logger.debug("---------------------------------------------------------------------------")
        logger.debug("Elapsed time for get_ai_state : {0}".format(end - start))
        logger.debug("---------------------------------------------------------------------------")

    except Exception as e:
        logger.critical("---------------------------------------------------------------------------")
        logger.critical("Error get_ai_state {0}".format(e))
        logger.critical("---------------------------------------------------------------------------")

    messages.append(
        dict(role="system", name="command", content=[return_type]))
    return messages


def do_query_command(command_messages):
    start = time.time()
    messages = [{
        "role": "system",
        "name": "assistant",
        "content": "You are a helpful assistant "

    }
    ]
    command_messages[0:0] = messages
    try:

        if use_model is not model_lama:
            completion = client_open_ai.chat.completions.create(
                model=use_model,
                temperature=0.7,
                messages=command_messages
            )

            command_messages.append(dict(role="assistant", name=ProcessType.QUERY.value,
                                         content=completion.choices[0].message.content))

        else:
            response = client_lama.chat(model=use_model,
                                        format="json",
                                        messages=command_messages)

            command_messages.append(dict(role="assistant", name=ProcessType.QUERY.value,
                                         content=response["message"]["content"]))

        end = time.time()

        logger.debug("---------------------------------------------------------------------------")
        logger.debug("Elapsed time for do_query_command : {0}".format(end - start))
        logger.debug("---------------------------------------------------------------------------")

    except Exception as e:
        logger.critical("---------------------------------------------------------------------------")
        logger.critical("Error do_query_command {0}".format(e))
        logger.critical("---------------------------------------------------------------------------")
        command_messages.append(
            dict(role="system", name="query_command", content='{"error":true,"message",e}'))
    return command_messages


def do_clear(self):
    self.data = []
    return True


def do_portfolio_command(messages):
    start = time.time()

    last_message = messages[len(messages) - 1]

    command_messages = [{
        "role": "system",
        "name": "assistant",
        "content": "You are a helpful assistant fluent in JSON designed to extract instructions to create a portfolio"
    },
        {
            "role": "system",
            "name": "assistant",
            "content": "Under no circumstances are you allowed to create a value for an attribute not found in the user query."
                       'The schema is : {"{"$schema":"http://json-schema.org/draft-04/schema#","type":"object","properties":{"ticker_info":{"type":"array","items":[{"type":"object","properties":{"error":{"type":"boolean"},"message":{"type":"string"},"ticker":{"type":"string"}},"required":["ticker","entries"]},{"type":"object","properties":{"ticker":{"type":"string"}},"required":["ticker"]}]},"start_date":{"type":"string"},"amount":{"type":"integer"}},"required":["ticker_info","start_date"]}'
        },
        last_message]
    try:

        completion = client_open_ai.chat.completions.create(
            model=use_model,
            response_format={"type": "json_object"},
            temperature=0.7,
            messages=command_messages
        )

        messages.append(
            dict(role="assistant", name="portfolio_command", content=json.loads(completion.choices[0].message.content)))


    except Exception as e:
        logger.critical("---------------------------------------------------------------------------")
        logger.critical("Error do_load_stock_quotes_command - get underlyings {0}".format(e))
        logger.critical("---------------------------------------------------------------------------")
        messages.append(
            dict(role="system", name="portfolio_command", content='{"error":true,"message",e}'))

    end = time.time()

    logger.debug("---------------------------------------------------------------------------")
    logger.debug("Elapsed time for do_portfolio_command : {0}".format(end - start))
    logger.debug("---------------------------------------------------------------------------")

    return messages
