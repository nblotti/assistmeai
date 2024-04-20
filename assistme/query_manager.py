import json
import time
from enum import Enum

from ollama import Client
from openai import OpenAI
import logging

from config import use_model, model_lama, ai_request_timeout

logger = logging.getLogger(__name__)
client_open_ai = OpenAI(timeout=ai_request_timeout)
client_lama = Client(host='http://192.168.1.5:32141')



def process_query(messages):
    start = time.time()
    message = [{
        "role": "system",
        "name": "assistant",
        "content": "You are a helpful assistant "

    }
    ]
    messages[0:0] = message
    try:

        if use_model is not model_lama:
            completion = client_open_ai.chat.completions.create(
                model=use_model,
                temperature=0.7,
                messages=messages
            )

            messages.append(dict(role="assistant", name="query",
                                         content=completion.choices[0].message.content))

        else:
            response = client_lama.chat(model=use_model,
                                        format="json",
                                        messages=messages)

            messages.append(dict(role="assistant", name="query",
                                         content=response["message"]["content"]))

        end = time.time()

        logger.debug("---------------------------------------------------------------------------")
        logger.debug("Elapsed time for do_query_command : {0}".format(end - start))
        logger.debug("---------------------------------------------------------------------------")

    except Exception as e:
        logger.critical("---------------------------------------------------------------------------")
        logger.critical("Error do_query_command {0}".format(e))
        logger.critical("---------------------------------------------------------------------------")
        messages.append(
            dict(role="system", name="query_command", content='{"error":true,"message",e}'))
    return messages


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
