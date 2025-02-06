import os

from langchain_community.document_loaders.parsers.audio import AzureOpenAIWhisperParser
from langchain_openai import AzureChatOpenAI

chat_gpt_4o_mini = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_4o_MINI_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_4o_MINI_CHAT_DEPLOYMENT_NAME"],
    tiktoken_model_name=os.environ["AZURE_GPT_4o_MINI_CHAT_MODEL_NAME"],

)

chat_gpt_4 = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_4_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_4_CHAT_DEPLOYMENT_NAME"],
    tiktoken_model_name=os.environ["AZURE_GPT_4_CHAT_MODEL_NAME"],
)

chat_gpt_4o = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_4o_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_4o_CHAT_DEPLOYMENT_NAME"],
    tiktoken_model_name=os.environ["AZURE_GPT_4o_CHAT_MODEL_NAME"],
)

whisper = AzureOpenAIWhisperParser(
    api_version=os.environ["AZURE_WHISPER_API_VERSION"],
    deployment_name=os.environ["AZURE_WHISPER_DEPLOYMENT_NAME"],
)
