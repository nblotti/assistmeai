import os

from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    openai_api_version=os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"]
)
