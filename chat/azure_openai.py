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

chat_gpt_o1 = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_O1_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_O1_CHAT_DEPLOYMENT_NAME"],
    tiktoken_model_name=os.environ["AZURE_GPT_O1_CHAT_MODEL_NAME"],
)

chat_gpt_o3_mini = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_O3_MINI_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_O3_MINI_CHAT_DEPLOYMENT_NAME"],
    tiktoken_model_name=os.environ["AZURE_GPT_O3_MINI_CHAT_MODEL_NAME"],
)

whisper = AzureOpenAIWhisperParser(
    api_version=os.environ["AZURE_WHISPER_API_VERSION"],
    deployment_name=os.environ["AZURE_WHISPER_DEPLOYMENT_NAME"],
)

chat_models = {"4": chat_gpt_4, "4o": chat_gpt_4o, "4om": chat_gpt_4o_mini, "o1": chat_gpt_o1,
               "o3-mini": chat_gpt_o3_mini}
