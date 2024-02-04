import json
import time
from datetime import datetime, date
from enum import Enum

from jsonpath_ng import parse

import requests
from openai import OpenAI
from statemachine import StateMachine, State
import logging

from assistme.models import Transcript
from assistmeai.config import model_get_ai_state, model_do_client, model_do_memo, \
    model_do_query, model_do_speach_to_text, model_do_load_stock_quotes, WEBEX_API_KEY, words_not_in_model, \
    model_do_product, solr_server, assistme_server, ai_request_timeout
from assistme.eod_repository import EodDataRepository


class CommandManager(StateMachine):
    # class variable

    solr_client_api_url = solr_server + "select?indent=true&q.op=AND&q=type:client"
    solr_memos_api_url = solr_server + "select?indent=true&q.op=OR&q="
    webex_api_url = "https://webexapis.com/v1/recordings"
    webex_api_detail_url = "https://webexapis.com/v1/recordings/{0}"
    document_api_url = assistme_server + "/api/requesttexttospeach/"

    product_api_url = solr_server + "select?indent=true&select&q.op=OR&q={0}"

    eodDataRepository = EodDataRepository()

    # states and state maching configuration
    waiting_for_command = State(initial=True)
    check_command_state = State()

    clear_state = State()
    done_state = State(final=True)

    do_check_command = waiting_for_command.to(check_command_state, on="command_marshalling")

    run_command = (check_command_state.to(done_state, unless="in_error", cond="is_client_process",
                                          on="do_client_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_memo_process",
                                          on="do_memo_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_load_webex_process",
                                          on="do_load_webex_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_speech_to_text_process",
                                          on="do_speach_to_text_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_load_stock_quotes_process",
                                          on="do_load_stock_quotes_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_load_product_process",
                                          on="do_product_command", after="check_error") |
                   check_command_state.to(done_state, unless="in_error", cond="is_query_process",
                                          on="do_query_command", after="check_error") |
                   check_command_state.to(clear_state, unless="in_error", cond="is_clear_process",
                                          on="do_clear", after="check_error")
                   )

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=WEBEX_API_KEY, timeout=ai_request_timeout)
        self.jwt = 0
        self.type = ProcessType.QUERY
        self.data = []
        self.wbx_jwt_token = ""
        self.in_error = False
        super().__init__()

    def check_error(self):
        if self.in_error:
            self.data.append(dict(role="system", name="error_state", content=""))

    def clearSystemMessages(self, messages):
        messages[:] = [message for message in messages if
                       not (message["role"] == "system" and "name" in message and message["name"] == "assistant")]

    def command_marshalling(self, current_messages, wbx_jwt_token, firebase_token, domain_header):

        self.wbx_jwt_token = wbx_jwt_token
        self.firebase_token = firebase_token
        self.clearSystemMessages(current_messages)

        query_str = current_messages[::-1][0]["content"].lower()

        self.type = None
        if "load" in query_str:
            if "memo" in query_str or "memos" in query_str :
                self.type = ProcessType.LOAD_MEMO
            elif "client" in query_str or "clients" in query_str:
                self.type = ProcessType.LOAD_CLIENT
            elif "webex" in query_str or "recording" in query_str:
                self.type = ProcessType.LOAD_WEBEX
            if "data" in query_str:
                self.type = ProcessType.LOAD_STOCK_QUOTE_DATA
            if "product" in query_str or "products" in query_str:
                self.type = ProcessType.LOAD_PRODUCT
        elif "speech to text" in query_str or "stt" in query_str:
            self.type = ProcessType.SPEECH_TO_TEXT
        elif "summary" in query_str:
            self.type = ProcessType.QUERY
        elif "clear" in query_str:
            self.type = ProcessType.CLEAR

        try:

            if not self.type:
                if not self.get_ai_state(current_messages[len(current_messages) - 1]):
                    return False

            for message in current_messages:
                if ((type == ProcessType.LOAD_CLIENT and message["name"] == "clients") or
                        (type == ProcessType.LOAD_MEMO and message["name"] == "memos")):
                    current_messages.remove(message)

            self.data = current_messages
            self.get_ids(current_messages)


        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error command_marshalling {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def get_ai_state(self, current_message):

        start = time.time()

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are helpfull assistant who will be presented with a message and your job is to provide a "
                       "JSON object with two attributes : state and reason"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "Choose a single state based ONLY from the list of state provided here :"
                           "here:"
                           "-load_memo"
                           "-load_client"
                           "-load_product"
                           "-load_webex"
                           "-query"
                           "-speech_to_text"
                           "-load_stock_quotes_state"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Some examples : "
                           "if the query is give me infos for Humphrey, return "
                           "{'state':'load_client','reason':'Humphrey is not a listed company "
                           "and info is not a synonym for memo'}"
                           "if the query is give me the contacts for Humphrey, return "
                           "{'state':'load_memo','reason':'contact and memos are synonyms'}"
                           "if the query is give me the info for apple last six months, return "
                           "{'state':'load_stock_quotes_state','reason':'aaple is  a listed company and no mention "
                           "of client or memo is found'}"
                           "if the query is give me the contacts for Cotton, return "
                           "{'state':'load_memos','reason':'Commodities are not managed and contacts and memos are "
                           "synonyms'}"
                            "if the query is give me infos for Cotton, return"
                           "{'state':'load_client','reason':'Commodities are not managed'}"
                           "if the query is what do the analysts think of the Apple"
                           "{'state':'query','reason':'Analysis is required.'}"
                           "if the query is give me the products who have Facebook as an underlying"
                           "{'state':'load_product','reason':'Although Facebook is a listed company, the user requested"
                           "a list of products and products are not listed'}"

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
            self.type = ProcessType(last_message["state"])

            end = time.time()

            self.logger.debug(last_message["reason"])
            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for get_ai_state : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")


        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error get_ai_state {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
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
        if self.type == ProcessType.LOAD_CLIENT:
            return True
        return False

    def is_memo_process(self):
        if self.type == ProcessType.LOAD_MEMO:
            return True
        return False

    def is_clear_process(self):
        if self.type == ProcessType.CLEAR:
            return True
        return False

    def is_load_webex_process(self):
        if self.type == ProcessType.LOAD_WEBEX:
            return True
        return False

    def is_query_process(self):
        if self.type == ProcessType.QUERY:
            return True
        return False

    def is_speech_to_text_process(self):
        if self.type == ProcessType.SPEECH_TO_TEXT:
            return True
        return False

    def is_load_stock_quotes_process(self):
        if self.type == ProcessType.LOAD_STOCK_QUOTE_DATA:
            return True
        return False

    def is_load_product_process(self):
        if self.type == ProcessType.LOAD_PRODUCT:
            return True
        return False

    def do_client_command(self):

        start = time.time()

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
                           "Don't consider the word in the following list :" + words_not_in_model + "to build the query"
                                                                                                    "or the filter"
                                                                                                    "Never use a value without the parameter name"
                                                                                                    "For every value use only one word. Never take the verb"
                                                                                                    "The country parameter is an existing country name. Do not use *.*"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Words starting with a capital letter are client's names. When query contain's a "
                           "capital letter, use name parameter for names"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Start string parameters in the query with /.* and finish with .*/."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "For age related questions, use birthDate parameter and format [* TO YYYY-MM-ddT00:00:00Z ]."
                           "Replace only date variable not the NOW variable. "
                           "Dont use relative variable. Do not apply range"
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

            self.logger.debug(api_url)
            result = dict(type=ProcessType.LOAD_CLIENT.value, content=
            requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="clients", content=json.dumps(result)))
            self.clearSystemMessages(self.data)

            end = time.time()

            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for do_client_command : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_memo_command {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def do_memo_command(self):

        start = time.time()
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
                "content": "Never use a value without the parameter name in the query"
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
                           "Don't consider the word in the following list :" + words_not_in_model + "to build the "
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
                           "the end of the parameter name. This rule does not apply for the memoContent parameter "
                           "used in the filter"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Words starting with a capital letter are client's names. When query contain's a capital "
                           "letter. Use name_str parameter for names not memoContent"
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

            self.logger.debug(api_url)
            self.logger.debug(api_filter)
            self.logger.debug(reason)
            if api_filter:
                if self.ids and not self.ids.__eq__('None'):
                    api_url += api_filter + " and clientId:" + self.ids
                else:
                    api_url += api_filter
            elif self.ids and not self.ids.__eq__('None'):
                api_url += "&fq=clientId:(" + self.ids + ")"

            result = dict(type=ProcessType.LOAD_MEMO.value,
                          content=requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="memos", content=json.dumps(result)))
            self.clearSystemMessages(self.data)

            end = time.time()

            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for do_memo_command : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_memo_command {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def do_query_command(self):

        start = time.time()
        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to produce json"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "Reply only to the last question"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Only use the last message in our conversation that has an attribute name containing value "
                           "'clients' to answer questions about clients"
            }
            ,
            {
                "role": "system",
                "name": "assistant",
                "content": "Only use the last message in our conversation that has an attribute name containing value "
                           "'memos' to answer questions about memos."
            }

        ]
        self.data[0:0] = messages
        try:

            completion = self.client.chat.completions.create(
                model=model_do_query,
                temperature=0.7,
                messages=self.data
            )

            self.data.append(dict(role="assistant", name=ProcessType.QUERY.value,
                                  content=json.dumps(completion.choices[0].message.content)))
            self.clearSystemMessages(self.data)

            end = time.time()

            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for do_query_command : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_query_command {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def do_clear(self):
        self.data = []
        return True

    def do_product_command(self):

        start = time.time()
        message = self.data[len(self.data) - 1]

        messages = [

            {
                "role": "system",
                "name": "assistant",
                "content": "You are a helpful assistant designed to produce json"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Never use a value without the parameter name in the query. A value cannot be used for "
                           "a parameter and a filter at the same time. Don't use two parameters for the same value. "
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "classify the parameters using the names in triple single quotes. The type of the parameter "
                           "is indicated between parenthesis following the name :'''subtype(string)''',"
                           "'''coupon(numeric)''','''underlyings(strings)''','''currency(string)''', "
                           "'''echeance(date)''','''ISIN(string)''','''strike_level(numeric)''',"
                           "'''barrier_level(numeric)''','''initial_fixing_date(date)''','''final_fixing_date(date)''',"
                           "'''total_expense_ratio(numeric)''','''kid_content(string)''','''term_content(string)'''"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Based on the classified parameters, build the query in the form 'parameter:value' "
                           "separated by ' AND '. Don't create parameters not existing in the parameter list."
                           "A parameter cannot appear more than once in the query. Never use a value without the "
                           "parameter name.For every value use only one word. Never take the verb. Do not use *.*"

            },
            {
                "role": "system",
                "name": "assistant",
                "content": "Examples : If the query is : give me the product with underlying apple or ams  and a "
                           "coupon bigger than 2% and a final fixing date before 2025 the query would be   "
                           "'''type:product AND underlyings:(ams* Adidas*) and coupon: [4 TO *]and final_fixing_date: "
                           "[* TO 2024-12-31T00:00:00Z ]'''If the query is : give me the products "
                           "return  '''type:product'''"
            },
            message]

        try:
            completion = self.client.chat.completions.create(
                model=model_do_product,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=messages
            )

            query = json.loads(completion.choices[0].message.content)["query"]

            api_url = self.product_api_url.format(query)

            self.logger.debug(api_url)
            result = dict(type=ProcessType.LOAD_PRODUCT.value,
                          content=requests.get(api_url).json()["response"]["docs"])
            self.data.append(dict(role="system", name="products", content=json.dumps(result)))

            end = time.time()

            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for do_product_command : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_product_command {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def do_load_webex_command(self):

        start = time.time()

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
            result = requests.get(CommandManager.webex_api_url, params=parameters, headers={
                "Authorization": "Bearer {0}".format(self.wbx_jwt_token)}).json()

            details = []
            for item in result["items"]:
                detail = requests.get(CommandManager.webex_api_detail_url.format(item["id"]), headers={
                    "Authorization": "Bearer {0}".format(self.wbx_jwt_token)}).json()
                details.append(detail)

            result = dict(type=ProcessType.LOAD_WEBEX.value, content=details)
            self.data.append(dict(role="system", name="webex", content=json.dumps(result)))

            end = time.time()

            self.logger.debug("---------------------------------------------------------------------------")
            self.logger.debug("Elapsed time for do_load_webex_command : {0}".format(end - start))
            self.logger.debug("---------------------------------------------------------------------------")

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_load_webex_command {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False
        return True

    def do_speach_to_text_command(self):

        start = time.time()

        last_message = {
            "role": "user",
            "content": json.dumps(self.data)
        }

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to select appropriate message from the message with name "
                       "webex and produce JSON"
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
        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_speach_to_text_command - select message {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False

        try:
            obj = Transcript.objects.create_transcript(document_id, self.firebase_token)
            obj.save()
            myobj = {'url': url, 'id': obj.id, 'document_id': document_id, 'format': format}
            response = requests.post(CommandManager.document_api_url,
                                     headers={'FIREBASETOKEN': self.firebase_token}, json=myobj)

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_speach_to_text_command - starting conversiont process {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False

        application_message = {
            "role": "system",
            "name": ProcessType.SPEECH_TO_TEXT.value,
            "content": str(obj.id)
        }
        self.data.append(application_message)
        self.clearSystemMessages(self.data)
        end = time.time()

        self.logger.debug("---------------------------------------------------------------------------")
        self.logger.debug("Elapsed time for do_speach_to_text_command : {0}".format(end - start))
        self.logger.debug("---------------------------------------------------------------------------")

        return True

    def do_load_stock_quotes_command(self):

        start = time.time()

        messages = [{
            "role": "system",
            "name": "assistant",
            "content": "You are a helpful assistant designed to extract the stock ticker , the market where the stock "
                       "is traded and the difference between date given and return them into JSON"
        },
            {
                "role": "system",
                "name": "assistant",
                "content": "return a structure in the form {ticker: value, market: value, from_date: value, "
                           "to_date: value, period:value, difference:value}"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If the stock is traded the USA, set market= 'us' "
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If the ticker contains a '.' split it : the part before the '.'' is the ticker value, "
                           "the part after is th market value"
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "For date use format [YYYY-MM-dd]."
            },
            {
                "role": "system",
                "name": "assistant",
                "content": "If you don't find date, use [2000-01-01] for from_date and today as to_date. Use" +
                           str(date.today()) + " as today"
            },
            self.data[len(self.data) - 1]
        ]
        try:

            completion = self.client.chat.completions.create(
                model=model_do_load_stock_quotes,
                response_format={"type": "json_object"},
                temperature=0.7,
                messages=messages
            )

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_load_stock_quotes_command - get underlyings {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            in_error = True
            return False

        try:

            data = json.loads(completion.choices[0].message.content)

            from_date = datetime.strptime(data["from_date"], "%Y-%m-%d")
            to_date = datetime.strptime(data["to_date"], "%Y-%m-%d")
            mk_qd_data = self.eodDataRepository.get_eod_stock_data(data["ticker"], data["market"],
                                                                   from_date, to_date)

            result = dict(type="load_stock_quotes_state",
                          content=mk_qd_data)
            self.data.append(dict(role="system", name="market_data", content=json.dumps(result)))

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_load_stock_quotes_command - load_stock_quotes_state {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False

        try:

            mk_fdata = self.eodDataRepository.get_eod_fundamental_data(data["ticker"], data["market"])
            result = dict(type="load_stock_fundamentals_state",
                          content=mk_fdata)
            self.data.append(dict(role="system", name="market_data", content=json.dumps(result)))

        except Exception as e:
            self.logger.critical("---------------------------------------------------------------------------")
            self.logger.critical("Error do_load_stock_quotes_command - load_stock_fundamentals_state {0}".format(e))
            self.logger.critical("---------------------------------------------------------------------------")
            self.in_error = True
            return False

        self.clearSystemMessages(self.data)
        end = time.time()

        self.logger.debug("---------------------------------------------------------------------------")
        self.logger.debug("Elapsed time for do_load_stock_quotes_command : {0}".format(end - start))
        self.logger.debug("---------------------------------------------------------------------------")

        return True


class ProcessType(Enum):
    LOAD_MEMO = 'load_memo'
    LOAD_CLIENT = 'load_client'
    LOAD_WEBEX = 'load_webex'
    SPEECH_TO_TEXT = 'speech_to_text'
    QUERY = 'query'
    CLEAR = 'clear'
    LOAD_STOCK_QUOTE_DATA = 'load_stock_quotes_state'
    LOAD_PRODUCT = 'load_product'
