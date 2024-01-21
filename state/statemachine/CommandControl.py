import json
import time
from datetime import datetime, date
from enum import Enum

import numpy
from jsonpath_ng import jsonpath, parse

import requests
from openai import OpenAI
from statemachine import StateMachine, State

from assistme.models import Transcript
from djangoProject.config import model_get_ai_state, model_do_client, model_do_memo, \
    model_do_query, model_do_speach_to_text, model_do_load_stock_quotes, WEBEX_API_KEY, words_not_in_model
from financialdata.eod.eod_data_repository import EodDataRepository


class PROCESS_TYPE(Enum):
    LOAD_MEMO = 'load_memo'
    LOAD_CLIENT = 'load_client'
    LOAD_WEBEX = 'load_webex'
    SPEECH_TO_TEXT = 'speech_to_text'
    QUERY = 'query'
    CLEAR = 'clear'
    LOAD_STOCK_QUOTE_DATA = 'load_stock_quotes_state'


class CommandControl(StateMachine):
    # class variable
    repository_api_url = "http://clientrepositories.nblotti.org/clients/"
    solr_client_api_url = "http://solr.nblotti.org/clients/select?indent=true&q.op=AND&q=type:client"
    solr_memos_api_url = "http://solr.nblotti.org/clients/select?indent=true&q.op=OR&q="
    webex_api_url = "https://webexapis.com/v1/recordings"
    webex_api_detail_url = "https://webexapis.com/v1/recordings/{0}"
    document_api_url = "https://assistmeai.nblotti.org/api/requesttexttospeach/"
    # document_api_url = "http://localhost:8000/api/requesttexttospeach/"


    eodDataRepository = EodDataRepository()

    # states and state maching configuration
    waiting_for_command = State(initial=True)
    check_command_state = State()
    client_state = State()
    memo_state = State()
    clear_state = State(enter="on_enter_do_clear", )
    load_webex_state = State()
    speech_to_text_state = State()
    load_stock_quotes_state = State()
    query_state = State()
    done_state = State(final=True)
    error_state = State(final=True)

    do_check_command = (
            waiting_for_command.to(check_command_state, cond="command_marshalling")
            | waiting_for_command.to(error_state, cond="in_error")
    )
    do_start_process = (
            check_command_state.to(client_state, cond="is_client_process")
            | check_command_state.to(memo_state, cond="is_memo_process")
            | check_command_state.to(clear_state, cond="is_clear_process")
            | check_command_state.to(load_webex_state, cond="is_load_webex_process")
            | check_command_state.to(speech_to_text_state, cond="is_speech_to_text_process")
            | check_command_state.to(load_stock_quotes_state, cond="is_load_stock_quotes_process")
            | check_command_state.to(query_state, cond="is_query_process")

    )
    do_query = (
            query_state.to(done_state, cond="do_query_command")
            | query_state.to(error_state, cond="in_error")
    )
    do_client = (
            client_state.to(done_state, cond="do_client_command")
            | client_state.to(error_state, cond="in_error")
    )

    do_memo = (
            memo_state.to(done_state, cond="do_memo_command")
            | memo_state.to(error_state, cond="in_error")
    )

    do_load_webex_state = (
            load_webex_state.to(done_state, cond="do_load_webex_command")
            | load_webex_state.to(error_state, cond="in_error")
    )

    do_text_to_speach_state = (
            speech_to_text_state.to(done_state, cond="do_speach_to_text_command")
            | speech_to_text_state.to(error_state, cond="in_error")
    )

    do_load_stock_quotes_state = (
            load_stock_quotes_state.to(done_state, cond="do_load_stock_quotes_command")
            | load_stock_quotes_state.to(error_state, cond="in_error")
    )


    do_clear = clear_state.to(done_state)

    def __init__(self):

        self.client = OpenAI(api_key=WEBEX_API_KEY)
        self.jwt = 0
        self.type = PROCESS_TYPE.QUERY
        self.data = []
        self.wbx_jwt_token = ""
        self.in_error = False
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
            if "memo" in query_str or "memos" in query_str:
                self.type = PROCESS_TYPE.LOAD_MEMO
            elif "client" in query_str or "clients" in query_str:
                self.type = PROCESS_TYPE.LOAD_CLIENT
            elif "webex" in query_str or "recording" in query_str:
                self.type = PROCESS_TYPE.LOAD_WEBEX
            if "data" in query_str:
                self.type = PROCESS_TYPE.LOAD_STOCK_QUOTE_DATA
        elif "text to speech" in query_str or "tts" in query_str:
            self.type = PROCESS_TYPE.SPEECH_TO_TEXT
        elif "summary" in query_str:
            self.type = PROCESS_TYPE.QUERY
        elif "clear" in query_str:
            self.type = PROCESS_TYPE.CLEAR


        if not self.type:
            if not self.get_ai_state(current_messages[len(current_messages)-1]):
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
            self.in_error = True
            return False
        return True

    def get_ai_state(self, current_message):

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are helpfull assistant who will be presented with a message and your job is to provide a "
                       "JSON object"
                       "with two attributes : state and reason"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "Choose a single state based ONLY from the list of state provided here :"
                           "here:"
                           "-load_memo"
                           "-load_client"
                           "-load_webex"
                           "-query"
                           "-speech_to_text"
                           "-load_stock_quotes_state"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "State cannot be 'load_memo' or  'load_client' when the last user message does not contains the word 'load' "

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "When a the last user message contains the word load and a ticker or a firm's name, set state to 'load_stock_quotes_state'"
                           "When a the last user message contains the word load and no ticker and no firm's name, set state to 'load_client'"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Use state 'load_client' for questions related to load commodity data"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Use state 'query' for questions related to market or stock analysis "

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Don't use load_memo state for mail and email tasks or any content creation. "
                           "A memo is a textual description of a meeting : a memo is not a mail or an email. "
                           "Use 'query' state for that"
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
                "content": "Use reason to explain your choice"
            },
            current_message

        ]


        completion = self.client.chat.completions.create(
            model=model_get_ai_state,
            response_format={"type": "json_object"},
            temperature=0.7,
            messages=messages

        )

        try:
            last_message = json.loads(completion.choices[0].message.content)
            self.type = PROCESS_TYPE(last_message["state"])
            print(last_message["reason"])

        except Exception as e:
            print(e)
            self.in_error = True
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

    def is_load_stock_quotes_process(self):
        if self.type == PROCESS_TYPE.LOAD_STOCK_QUOTE_DATA:
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
             "content": "First you need to match parameters and classify them following this parameter list : id("
                        "numeric),name(string),email(string),gender(string),country(string),"
                        "birthDate(date),vhni(boolean),pledge(boolean),alertDoubtful(boolean),alertRisk(boolean),"
                        "alertPendingOrder(boolean),alertOutstandingDocument(boolean),"
                        "alertNonStandardScale(boolean)"
             },
            {
                "role": "system",
                "name": "assistant",
                "content": "Based on the classified parameters, build the query in the form 'parameter:value' "
                           "separated by ' AND '. Don't create parameters not existing in the parameter list."
                           "A parameter cannot appear more than once in the query"
                          "Don't consider the word in the following list :" + words_not_in_model +"to build the query "
                                                                                                  "or the filter"
                           "Never use a value without the parameter name"
                           "For every value use only one word. Never take the verb"
                           "The country parameter is an existing country name. Do not use *.*"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Words starting with a capital letter are client's names. When query contain's a capital letter, use name parameter for names"
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
                           "Replace only date variable not the NOW variable. Dont use relative variable. Do not apply range"
            }]

        self.data[0:0] = messages

        try:
            completion = self.client.chat.completions.create(
                model=model_do_client,
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
            self.in_error = True
            return False
        return True

    def do_memo_command(self):

        messages = [
            {
                "role": "system",
                "name": "assistant",
                "content": "You are a helpful assistant designed to build an http encoded solr query "
                           "in the form : '{!join from=id to=clientId}parameter:value' and  a filter "
                           "in the form : '&fq=memoContent:value'"

            },
            {
                "role": "system",
                "name": "assistant",
                "content":              "Never use a value without the parameter name in the query"
                                        "A value cannot be used for a parameter and a filter at the same time."
                                        "Don't use two parameters for the same value. "
                                        "A contact is a memo, not a client or a type of memo"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "classify the query parameters as id(numeric),name_str(string),email(string), "
                           "gender(string), country(string),birthDate(date),vhni(boolean),pledge(boolean),"
                           "alertDoubtful(boolean),alertRisk(boolean),alertPendingOrder(boolean),"
                           "alertOutstandingDocument(boolean),alertNonStandardScale(boolean)"
                           "Don't create parameters not existing in the parameter list."
                           "Don't consider the word in the following list :" + words_not_in_model +"to build the "
                                                                                                   "query or the filter"
                           "The filter newer contains other parameter than memoContent"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you don't find no parameter at all set query = 'type:memo'"
                           "If you don't find any question related to the content, set filter = ''"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you don't find no parameter at all set query = 'type:memo'"
                           "If you don't find any question related to the content, set filter = ''"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If a part of the question is related to the content or the meaning of the document,"
                           "don't classify it, but add it to the filter instead"


            },
            {
                "role": "system",
                "name": "assistant",
                "content": "email  must contains character '@'. It is related to an email"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Start string parameters value in the query with /.* and finish with .*/. Add '_str' at "
                           "the end of the parameter name. This rule does not apply for the memoContent parameter used in the filter"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Words starting with a capital letter are client's names. When query contain's a capital letter. Use name_str parameter for names not memoContent"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "return response in a json in the form {q=query, f=filter, r=reason}."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "For birthDate use format [YYYY-MM-ddT00:00:00Z TO NOW] or [NOW TO "
                           "YYYY-MM-ddT00:00:00Z].Replace only date variable not the NOW variable. Do not apply range"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "use r to describe how you decided to classify each parameter"
            }
        ]
        try:
            self.data[0:0] = messages

            completion = self.client.chat.completions.create(
                model=model_do_memo,
                response_format={"type": "json_object"},
                temperature=0.5,
                messages=self.data
            )
            api_url = self.solr_memos_api_url + json.loads(completion.choices[0].message.content)["q"]
            api_filter = json.loads(completion.choices[0].message.content)["f"]
            reason = json.loads(completion.choices[0].message.content)["r"]

            print(api_url)
            print(api_filter)
            print(reason)
            if api_filter:
                if self.ids and not self.ids.__eq__('None'):
                    api_url += api_filter + " and clientId:" + self.ids
                else:
                    api_url += api_filter
            elif self.ids and not self.ids.__eq__('None'):
                api_url  += "&fq=clientId:(" + self.ids + ")"




            result = dict(type=PROCESS_TYPE.LOAD_MEMO.value,
                          content=requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="memos", content=json.dumps(result)))
            self.clearSystemMessages(self.data)
        except Exception as e:
            print(e)
            self.in_error = True
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
                model=model_do_query,
                temperature=0.7,
                messages=self.data
            )

            self.data.append(dict(role="assistant", name=PROCESS_TYPE.QUERY.value,
                                  content=json.dumps(completion.choices[0].message.content)))
            self.clearSystemMessages(self.data)
        except Exception as e:
            print(e)
            self.in_error = True
            return False
        return True

    def on_enter_do_clear(self):
        self.data = []
        return True

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
            self.in_error = True
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
                model=model_do_speach_to_text,
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
                print(e)
                self.in_error = True
                return False

            application_message = {
                "role": "system",
                "name": PROCESS_TYPE.SPEECH_TO_TEXT.value,
                "content": str(obj.id)
            }
            self.data.append(application_message)
            self.clearSystemMessages(self.data)

        except Exception as e:
            print(e)
            self.in_error = True
            return False
        return True

    def do_load_stock_quotes_command(self):

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to extract the stock ticker , the market where the stock is traded and the difference between date given and return them into JSON"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "return a structure in the form {ticker: value, market: value, from_date: value, to_date: value, period:value, difference:value}"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If the stock is traded the USA, set market= 'us' "
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If the ticker contains a '.' split it : the part before the '.'' is the ticker value, the part after is th market value"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "For date use format [YYYY-MM-dd]."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you don't find date, use [2000-01-01] for from_date and today as to_date. Use"+
                           str(date.today()) + " as today"
            },
            self.data[len(self.data)-1]
        ]
        try:

            completion = self.client.chat.completions.create(
                model=model_do_load_stock_quotes,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=messages
            )

        except Exception as e:
            print(e)
            self.in_error = True
            return False

        try:

            data = json.loads(completion.choices[0].message.content)

            from_date = datetime.strptime(data["from_date"], "%Y-%m-%d")
            to_date = datetime.strptime(data["to_date"], "%Y-%m-%d")
            mk_qd_data = self.eodDataRepository.get_eod_stock_data(data["ticker"], data["market"],
                                                                       from_date, to_date)

            result = dict(type=PROCESS_TYPE.LOAD_STOCK_QUOTE_DATA.value,
                          content=mk_qd_data)
            self.data.append(dict(role="system", name="market_data", content=json.dumps(result)))

        except Exception as e:
            print(e)
            self.in_error = True
            return False

        try:

            mk_fdata = self.eodDataRepository.get_eod_fundamental_data(data["ticker"], data["market"])
            result = dict(type=PROCESS_TYPE.LOAD_STOCK_QUOTE_DATA.value,
                          content=mk_fdata)
            self.data.append(dict(role="system", name="market_data", content=json.dumps(result)))

        except Exception as e:
            print(e)
            self.in_error = True
            return False

        self.clearSystemMessages(self.data)
        return True

