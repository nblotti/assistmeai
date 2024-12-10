import json
import os

from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector

from embeddings.azure_openai import embeddings


# We use postgresql rather than postgres in the conn string since LangChain uses sqlalchemy under the hood
# You can remove the ?sslmode=require if you have a local PostgreSQL instance running without SSL

vector_store = PGVector.from_existing_index(
    collection_name=os.getenv("POSTGRES_INDEX_NAME"),
    embedding=embeddings,
    connection=os.getenv("PGVECTOR_CONNECTION_STRING"),
    use_jsonb=True,
)


def build_all_documents_retriever(perimeter: str):
    filter_criteria = {'perimeter': {"$in": json.dumps(perimeter.split())}}

    # Convert the dictionary to a frozenset of sorted items
    hashable_filter_criteria = frozenset(sorted(filter_criteria.items()))

    # Construct search kwargs
    search_kwargs = {
        'filter': hashable_filter_criteria
    }

    # Construct the retriever with the search kwargs
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

    # Print for debugging
    print(retriever.search_kwargs)

    return retriever
