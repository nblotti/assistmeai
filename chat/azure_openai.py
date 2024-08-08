import os

from langchain_openai import  AzureChatOpenAI


chat_gpt_35 = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_35_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_35_CHAT_DEPLOYMENT_NAME"],
)

chat_gpt_4o = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_GPT_4_API_VERSION"],
    azure_deployment=os.environ["AZURE_GPT_4_CHAT_DEPLOYMENT_NAME"],
)


