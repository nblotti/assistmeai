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



def process_screen(messages):
    start = time.time()
    current_message = messages[len(messages) - 1]
    message = [{
      "role": "system",
      "content": "your are a useful assistant"
    },
    {
      "role": "user",
      "content": "Prompt: Write a set of instructions for a program that manipulates a screen divided into four "
                 "quadrants. Your task is to outline actions using natural language that concern merging, splitting, "
                 "or resizing quadrants, as well as adding or removing components, namely graphs or tables. Provide "
                 "examples of these operations, specifying the location (top or bottom) and optional percentage for "
                 "resizing, or quadrant number (1-4) for adding or removing components. Your response should be in "
                 "the form of a JSON structure with an attribute for the verb (merge, split, resize, add, remove), "
                 "location (top or bottom), an optional percentage for resizing, and an optional quadrant number for "
                 "adding or removing components. Instructions should be clear and concise, with multiple examples "
                 "provided for each operation.\n\nExample JSON structures:\n1. Merge operation:\n{\n  \"verb\": "
                 "\"merge\",\n  \"location\": \"top\"\n}\n2. Split operation:\n{\n  \"verb\": \"split\","
                 "\n  \"location\": \"bottom\"\n}\n3. Resize operation:\n{\n  \"verb\": \"resize\",\n  \"location\": "
                 "\"top\",\n  \"percentage\": 70\n}\n4. Add operation:\n{\n  \"verb\": \"add\","
                 "\n  \"quadrantNumber\": 2,\n  \"component\": \"graph\"\n}\n5. Remove operation:\n{\n  \"verb\": "
                 "\"remove\",\n  \"quadrantNumber\": 4,\n  \"component\": \"table\"\n}\n\nExamples of merging, "
                 "splitting, resizing, adding, and removing:\n- Merge Screen 1 and 4\n- Resize the top quadrant to "
                 "50% height\n- Split Screen 2 and 3\n- Add a graph to quadrant 2\n- Remove a table from quadrant "
                 "4\n- Merge Screen 1 and 4 with 30% from the top"
    },
        current_message
    ]
    try:

        if use_model is not model_lama:
            completion = client_open_ai.chat.completions.create(
                model=use_model,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=message
            )

            message.append(dict(role="assistant", name="query",
                                         content=completion.choices[0].message.content))

        else:
            response = client_lama.chat(model=use_model,
                                        format="json",
                                        messages=message)

            message.append(dict(role="assistant", name="query",
                                         content=response["message"]["content"]))

        end = time.time()

        logger.debug("---------------------------------------------------------------------------")
        logger.debug("Elapsed time for do_query_command : {0}".format(end - start))
        logger.debug("---------------------------------------------------------------------------")

    except Exception as e:
        logger.critical("---------------------------------------------------------------------------")
        logger.critical("Error do_query_command {0}".format(e))
        logger.critical("---------------------------------------------------------------------------")
        message.append(
            dict(role="system", name="query_command", content='{"error":true,"message",e}'))
    return message

