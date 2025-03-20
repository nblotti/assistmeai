import os

from langchain_openai import AzureOpenAIEmbeddings


def get_embeddings_and_set_env() -> AzureOpenAIEmbeddings:
    os.environ["AZURE_OPENAI_API_KEY"] = os.environ["AZURE_OPENAI_API_CH_KEY"]
    os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ["AZURE_OPENAI_CH_ENDPOINT"]

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"],
        openai_api_version=os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"]
    )

    return embeddings
