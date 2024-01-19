import json
from datetime import datetime
from enum import Enum
from jsonpath_ng import jsonpath, parse

import requests
from openai import OpenAI
from statemachine import StateMachine, State

from assistme.models import Transcript


class PROCESS_TYPE(Enum):
    LOAD_MEMO = 'load_memo'
    LOAD_CLIENT = 'load_client'
    LOAD_WEBEX = 'load_webex'
    SPEECH_TO_TEXT = 'speech_to_text'
    QUERY = 'query'
    CLEAR = 'clear'


class CommandControl(StateMachine):
    # class variable
    repository_api_url = "http://clientrepositories.nblotti.org/clients/"
    solr_client_api_url = "http://solr.nblotti.org/clients/select?indent=true&q.op=AND&q=type:client"
    solr_memos_api_url = "http://solr.nblotti.org/clients/select?indent=true&q.op=OR&q="
    webex_api_url = "https://webexapis.com/v1/recordings"
    webex_api_detail_url = "https://webexapis.com/v1/recordings/{0}"
    document_api_url = "https://assistmeai.nblotti.org/api/requesttexttospeach/"
    # document_api_url = "http://localhost:8000/api/requesttexttospeach/"
    model35 = "gpt-3.5-turbo-1106"
    model4 = "gpt-4-1106-preview"

    # states and state maching configuration
    waiting_for_command = State(initial=True)
    check_command_state = State()
    client_state = State()
    memo_state = State()
    clear_state = State(enter="on_enter_do_clear", )
    load_webex_state = State()
    speech_to_text_state = State()
    query_state = State()
    done_state = State(final=True)
    error_state = State(final=True)

    do_check_command = (
            waiting_for_command.to(check_command_state, cond="command_marshalling")
            | waiting_for_command.to(error_state, unless="command_marshalling")
    )
    do_start_process = (
            check_command_state.to(client_state, cond="is_client_process")
            | check_command_state.to(memo_state, cond="is_memo_process")
            | check_command_state.to(clear_state, cond="is_clear_process")
            | check_command_state.to(load_webex_state, cond="is_load_webex_process")
            | check_command_state.to(speech_to_text_state, cond="is_speech_to_text_process")
            | check_command_state.to(query_state, cond="is_query_process")

    )
    do_query = (
            query_state.to(done_state, cond="do_query_command")
            | query_state.to(error_state, unless="do_query_command")
    )
    do_client = (
            client_state.to(done_state, cond="do_client_command")
            | client_state.to(error_state, unless="do_client_command")
    )

    do_memo = (
            memo_state.to(done_state, cond="do_memo_command")
            | memo_state.to(error_state, unless="do_memo_command")
    )

    do_load_webex_state = (
            load_webex_state.to(done_state, cond="do_load_webex_command")
            | load_webex_state.to(error_state, unless="do_load_webex_command")
    )

    do_text_to_speach_state = (
            speech_to_text_state.to(done_state, cond="do_speach_to_text_command")
            | speech_to_text_state.to(error_state, unless="do_speach_to_text_command")
    )
    do_clear = clear_state.to(done_state)

    def __init__(self):

        self.client = OpenAI(api_key="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")
        self.jwt = 0
        self.type = PROCESS_TYPE.QUERY
        self.data = []
        self.wbx_jwt_token = ""
        self.ids = ""
        super(CommandControl, self).__init__()

    def clearSystemMessages(self, messages):
        messages[:] = [message for message in messages if
                       not (message["role"] == "system" and "name" in message and message["name"] == "assistant")]

    def command_marshalling(self, current_messages, wbx_jwt_token, firebase_token):

        self.wbx_jwt_token = wbx_jwt_token
        self.firebase_token = firebase_token

        self.clearSystemMessages(current_messages)

        query_str = current_messages[::-1][0]["content"].lower()

        self.type = None
        if "load" in query_str:
            if "client" in query_str or "clients" in query_str:
                self.type = PROCESS_TYPE.LOAD_CLIENT
            elif "memo" in query_str or "memos" in query_str:
                self.type = PROCESS_TYPE.LOAD_MEMO
            elif "webex" in query_str or "recording" in query_str:
                self.type = PROCESS_TYPE.LOAD_WEBEX
        elif "text to speech" in query_str or "tts" in query_str:
            self.type = PROCESS_TYPE.SPEECH_TO_TEXT
        elif "summary" in query_str:
            self.type = PROCESS_TYPE.QUERY
        elif "clear" in query_str:
            self.type = PROCESS_TYPE.CLEAR

        if not self.type:
            if not self.get_ai_state(current_messages):
                return False
        try:
            for message in current_messages:
                if ((type == PROCESS_TYPE.LOAD_CLIENT and message["name"] == "clients") or
                        (type == PROCESS_TYPE.LOAD_MEMO and message["name"] == "memos")):
                    current_messages.remove(message)

            self.data = current_messages
            self.get_ids(current_messages)

        except Exception as e:
            print(e)
            return False
        return True

    def get_ai_state(self, current_messages):
        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You will be presented with messages and your job is to provide a JSON object "
                       "with two attributes : state and reason"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "Choose state based ONLY from the list of state provided "
                           "here:"
                           "-load_memo"
                           "-load_client"
                           "-load_webex"
                           "-query"
                           "-speech_to_text"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "You have to return a state. Choose only from the state list do not create any other state. "
                           "You are not responsible to load data if requested to produce content"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "speech_to_text_state when 1. you see a message with 'name' = 'webex' in "
                           "history and 2. you're asked to transcript a webex meeting present in the message"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Don't use load_memo state for mail and email tasks or any content creation. A memo is a textual description of a meeting : a memo is not a mail or an email. Use query state for that"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If the query contains a reference to loading something state has to be 'to 'load_client', "
                           "'load_memo' or 'load_webex'"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you have a doubt, treat word starting with a capital letter as a name_str parameter"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Use reason to explain your choice"
            }

        ]

        messages[len(messages):len(messages)] = current_messages

        completion = self.client.chat.completions.create(
            model=CommandControl.model4,
            response_format={"type": "json_object"},
            temperature=0.7,
            messages=messages

        )

        try:
            last_message = json.loads(completion.choices[0].message.content)
            self.type = PROCESS_TYPE(last_message["state"])
            if "ids" in last_message:
                self.ids = last_message["ids"]
        except Exception as e:
            print(e)
            return False
        return True

    def get_ids(self, current_messages):

        client_message = None
        for message in current_messages:
            if message["role"] == "system" and message["name"] == "clients":
                client_message = json.loads(message["content"])
                break

        jsonpath_expression = parse('content[*].id')

        ids = []

        for match in jsonpath_expression.find(client_message):
            ids.append(match.value)

        self.ids = " ".join(ids)

    def is_client_process(self):
        if self.type == PROCESS_TYPE.LOAD_CLIENT:
            return True
        return False

    def is_memo_process(self):
        if self.type == PROCESS_TYPE.LOAD_MEMO:
            return True
        return False

    def is_clear_process(self):
        if self.type == PROCESS_TYPE.CLEAR:
            return True
        return False

    def is_load_webex_process(self):
        if self.type == PROCESS_TYPE.LOAD_WEBEX:
            return True
        return False

    def is_query_process(self):
        if self.type == PROCESS_TYPE.QUERY:
            return True
        return False

    def is_speech_to_text_process(self):
        if self.type == PROCESS_TYPE.SPEECH_TO_TEXT:
            return True
        return False

    def do_client_command(self):

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to build an http query and return it into JSON. "
                       "JSON returned should be in the form {result:query }"
        },

            {"role": "system",
             "name": "assistant",
             "content": "First you need to match parameters and classify them following this parameter list : id(numeric),name_str(string),email_str(string),address_str(string),gender_str(string),country_str(string),"
                        "birthDate(date),vhni(boolean),pledge(boolean),alertDoubtful(boolean),alertRisk(boolean),alertPendingOrder(boolean),alertOutstandingDocument(boolean),"
                        "alertNonStandardScale(boolean)"
             },
            {
                "role": "system",
                "name": "assistant",
                "content": "Based on the classified parameters, build the query in the form 'parameter:value' "
                           "Don't create parameters not existing in the parameter list."
                           "separated by ' AND '. Don't use parameters not found in the query."
                           "A parameter cannot appear more than once in the query"
                           "Never use a value without the parameter name"
                           "For every value use only one word. Never take the verb"
                           "If you have a doubt, treat word starting with a capital letter as a name_str parameter"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Start string parameters in the query with /.* and finish with .*/."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "For age related questions, use birthDate parameter and format [* TO YYYY-MM-ddT00:00:00Z ]. "
                           "Replace only date variable not the NOW variable. Dont use relative variable"
            }]

        self.data[0:0] = messages

        try:
            completion = self.client.chat.completions.create(
                model=CommandControl.model4,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=self.data
            )

            request_params = json.loads(completion.choices[0].message.content)["result"]

            if request_params:
                api_url = "{0} AND {1}".format(self.solr_client_api_url, request_params)
            else:
                api_url = self.solr_client_api_url
            print(api_url)
            result = dict(type=PROCESS_TYPE.LOAD_CLIENT.value, content=
            requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="clients", content=json.dumps(result)))
            self.clearSystemMessages(self.data)
        except Exception as e:
            print(e)
            return False
        return True

    def do_memo_command(self):

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed only to build an http encoded solr query and a filter and return it into JSON"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "first you need to match parameters and classify them as id(numeric),name(string),email(string),address(string), gender(string), country(string),"
                           "birthDate(date),vhni(boolean),pledge(boolean),alertDoubtful(boolean),alertRisk(boolean),alertPendingOrder(boolean),alertOutstandingDocument(boolean),"
                           "alertNonStandardScale(boolean),contactContent(text)."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "contactContent is related to the content and the meaning of the memo. It is not an alert or an attribute of the client. "
                           "name is related to the client name or part of the client name"
                           "email  must contains character '@'. It is related to an email"
            }, {
                "role": "system",
                "name": "assistant",
                "content": "If you find other parameters than contactContent, build a query in the form '{!join from=id to=clientId}parameter:value'"
                           "Do not include parameters classified as contactContent."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you find no parameters or only parameters classified as contactContent, query is 'type:contact'"
            }, {
                "role": "system",
                "name": "assistant",
                "content": "If you find a parameter classified as contactContent, build a solr filter parameter in the form '&fq=contactContent:value'"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "return response in a json in the form {q=query, f=filter}parameter:value. Never use a value without the parameter name"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Start string parameters value in the query with /.* and finish with .*/. Add '_str' at the end of the parameter name"
            }
            ,
            {
                "role": "system",
                "name": "assistant",
                "content": "For birthDate use format [YYYY-MM-ddT00:00:00Z TO NOW] or [NOW TO "
                           "YYYY-MM-ddT00:00:00Z].Replace only date variable not the NOW variable."
            }
        ]
        try:
            self.data[0:0] = messages

            completion = self.client.chat.completions.create(
                model=CommandControl.model4,
                response_format={"type": "json_object"},
                temperature=0.5,
                messages=self.data
            )
            api_url = self.solr_memos_api_url + json.loads(completion.choices[0].message.content)["q"]
            api_filter = json.loads(completion.choices[0].message.content)["f"]

            if api_filter and self.ids and not self.ids.__eq__('None'):
                api_filter = api_filter + " and clientId:" + self.ids
            elif self.ids and not self.ids.__eq__('None'):
                api_filter += "&fq=clientId:(" + self.ids + ")"

            api_url = api_url + api_filter
            print(api_url)

            result = dict(type=PROCESS_TYPE.LOAD_MEMO.value,
                          content=requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="memos", content=json.dumps(result)))
            self.clearSystemMessages(self.data)
        except Exception as e:
            print(e)
            return False
        return True

    def do_query_command(self):

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant to produce json"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "Reply only to the last question"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Only use the last message in our conversation that has an attribute name containing value 'clients' to answer questions about clients"
            }
            ,
            {
                "role": "system",
                "name": "assistant",
                "content": "Only use the last message in our conversation that has an attribute name containing value 'memos' to answer questions about memos."
            }

        ]
        self.data[0:0] = messages
        try:

            completion = self.client.chat.completions.create(
                model=CommandControl.model4,
                temperature=0.7,
                messages=self.data
            )

            self.data.append(dict(role="assistant", name=PROCESS_TYPE.QUERY.value,
                                  content=json.dumps(completion.choices[0].message.content)))
            self.clearSystemMessages(self.data)
        except Exception as e:
            print(e)
            return False
        return True

    def on_enter_do_clear(self):
        self.data = []

    def do_load_webex_command(self):

        if self.wbx_jwt_token is None:
            command = json.dumps(dict(command="login_webex"))
            application_message = {
                "role": "assistant",
                "name": "login_webex",
                "content": command
            }
            self.data.append(application_message)
            return

        parameters = []
        parameters = {'from': '2020-01-01', 'to': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}

        try:
            result = requests.get(CommandControl.webex_api_url, params=parameters, headers={
                "Authorization": "Bearer {0}".format(self.wbx_jwt_token)}).json()

            details = []
            for item in result["items"]:
                detail = requests.get(CommandControl.webex_api_detail_url.format(item["id"]), headers={
                    "Authorization": "Bearer {0}".format(self.wbx_jwt_token)}).json()
                details.append(detail)

            result = dict(type=PROCESS_TYPE.LOAD_WEBEX.value, content=details)
            self.data.append(dict(role="system", name="webex", content=json.dumps(result)))
        except Exception as e:
            print(e)
            return False
        return True

    def do_speach_to_text_command(self):

        last_message = {
            "role": "user",
            "content": json.dumps(self.data)
        }

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to select appropriate message from the message with name webex and produce JSON"
        }, {
            "role": "system",
            "name": "assistant",
            "content": "Return a json in the form {url=attribute recordingDownloadLink, id=id, format=format}"
        }, {
            "role": "system",
            "name": "assistant",
            "content": "Only use the last user message to find messageId"
        }, last_message]

        try:
            completion = self.client.chat.completions.create(
                model=CommandControl.model35,
                response_format={"type": "json_object"},
                temperature=0.3,
                messages=messages
            )

            url = json.loads(completion.choices[0].message.content)["url"]
            document_id = json.loads(completion.choices[0].message.content)["id"]
            format = json.loads(completion.choices[0].message.content)["format"]

            try:
                obj = Transcript.objects.create_transcript(document_id, self.firebase_token)
                obj.save()
                myobj = {'url': url, 'id': obj.id, 'document_id': document_id, 'format': format}
                response = requests.post(CommandControl.document_api_url,
                                         headers={'FIREBASETOKEN': self.firebase_token}, json=myobj)

            except Exception as e:
                return False

            application_message = {
                "role": "system",
                "name": PROCESS_TYPE.SPEECH_TO_TEXT.value,
                "content": str(obj.id)
            }
            self.data.append(application_message)

        except Exception as e:
            print(e)
            return False
        return True
