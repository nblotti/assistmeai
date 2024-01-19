from openai import OpenAI
import json
import requests


class ClientLoader:
    def __init__(self):
        self.client = OpenAI(api_key="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")

    def do_contact_command(self, message):

        messages = [{
            "role": "system",
            "content": "You are a helpful assistant designed to build an http encoded solr query and return it into JSON"
        }, {
            "role": "system",
            "content": "the only list of  parameters are :  id,name,email,address,gender,country,birthDate,vhni,pledge,alertDoubtful,alertRisk,alertPendingOrder,alertOutstandingDocument,alertNonStandardScale"
        }, {
            "role": "system",
            "content": "query is in the form {!join from=id to=clientId}parameter:value"
        },
            {
                "role": "system",
                "content": "return response in a json in the form {q=response}"
            },
            {
                "role": "system",
                "content": "For contactDate use format [YYYY-MM-ddT00:00:00Z TO NOW] or [NOW TO YYYY-MM-ddT00:00:00Z].. Replace only date variable not the NOW variable."
            },
                message[len(message) - 1]
        ]

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            temperature=0.1,
            messages=messages

        )
        try:
            api_url = "http://solr.nblotti.org/clients/select?indent=true&q.op=OR&q="+json.loads(completion.choices[0].message.content)["q"]

            return dict(type="contacts", content=requests.get(api_url).json()["response"]["docs"])

        except Exception as e:
            print(e)
            return False
