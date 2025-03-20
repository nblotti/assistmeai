import os

from langchain_community.document_loaders.parsers.audio import AzureOpenAIWhisperParser
from langchain_openai import AzureChatOpenAI


def get_model_and_set_env(model_name: str) -> AzureChatOpenAI | AzureOpenAIWhisperParser:
    # Set environment variables for Sweden deployment if 'o1' or 'o3-mini'
    if model_name in ("o1", "o3-mini"):
        os.environ["AZURE_OPENAI_API_KEY"] = os.environ["AZURE_OPENAI_SWEDEN_API_KEY"]
        os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ["AZURE_OPENAI_SWEDEN_ENDPOINT"]
    else:
        # Reset to initial values
        os.environ["AZURE_OPENAI_API_KEY"] = os.environ["AZURE_OPENAI_API_CH_KEY"]
        os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ["AZURE_OPENAI_CH_ENDPOINT"]

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
        openai_api_version=os.environ["AZURE_GPT_01_API_VERSION"],
        azure_deployment=os.environ["AZURE_GPT_01_CHAT_DEPLOYMENT_NAME"],
        tiktoken_model_name=os.environ["AZURE_GPT_01_CHAT_MODEL_NAME"],
        temperature=1
    )

    chat_gpt_o3_mini = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_GPT_03_MINI_API_VERSION"],
        azure_deployment=os.environ["AZURE_GPT_03_MINI_CHAT_DEPLOYMENT_NAME"],
        tiktoken_model_name=os.environ["AZURE_GPT_03_MINI_CHAT_MODEL_NAME"],
        temperature=1
    )

    whisper = AzureOpenAIWhisperParser(
        api_version=os.environ["AZURE_WHISPER_API_VERSION"],
        deployment_name=os.environ["AZURE_WHISPER_DEPLOYMENT_NAME"],
    )

    # Dictionary of supported models
    chat_models = {
        "4": chat_gpt_4,
        "4o": chat_gpt_4o,
        "4o-mini": chat_gpt_4o_mini,
        "whisper": whisper,
        "o1": chat_gpt_o1,
        "o3-mini": chat_gpt_o3_mini,
    }

    # Validate model_name and retrieve model
    if model_name not in chat_models:
        raise ValueError(f"Invalid model name '{model_name}'. Available models: {', '.join(chat_models.keys())}.")

    model = chat_models[model_name]

    return model
