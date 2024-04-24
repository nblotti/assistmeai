import os

from dotenv import load_dotenv
import pinecone
from langchain_community.vectorstores import Pinecone

from embeddings.openai import embeddings

load_dotenv()

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

vector_store = Pinecone.from_existing_index(
    index_name=os.getenv("PINECONE_INDEX_NAME"),
    embedding=embeddings
)


def build_specific_document_retriever(user_id: str, blob_id: str):
    return vector_store.as_retriever(
        search_kwargs={

            'filter': {
                'blob_id': {"$eq": blob_id},
                'user_id': user_id
            }
        }
    )


def build_all_documents_retriever(user_id: str):
    return vector_store.as_retriever(
        search_kwargs={

            'filter': {
                'user_id': user_id
            }
        }
    )
