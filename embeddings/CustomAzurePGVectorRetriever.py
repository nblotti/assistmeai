import logging
from dataclasses import field
from typing import List, Any, Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from embeddings.PGVectorStore import vector_store
from embeddings.QueryType import QueryType


class CustomAzurePGVectorRetriever(BaseRetriever):
    filter: dict = field(default_factory=dict)
    k: Optional[int] = 10

    def __init__(self, query_type: QueryType, value: str, k: int = 10, **kwargs: Any):
        super().__init__(**kwargs)

        if k != -1:
            self.k = k
        else:
            self.k = None

        if query_type == QueryType.DOCUMENT:
            self.filter = {'blob_id': {"$eq": value}}
        elif query_type == QueryType.DOCUMENTS:
            self.filter = self.create_in_query_filter(value)
        else:
            self.filter = self.create_combined_filter(value)

    def create_like_query_array(self, input_string):
        # Split the input string into a list of words
        words = input_string.split()

        # Create a list of dictionaries based on the required format
        query_array = [{'perimeter': {"$like": f"%/{word}/%"}} for word in words]

        return query_array

    def create_in_query_filter(self, input_string):
        # Split the input string into a list of words
        words = input_string.split(",")

        # Create a list of dictionaries based on the required format
        query_array = {'blob_id': {"$in": [f"{word}" for word in words]}}
        logging.error(query_array)
        return query_array

    def create_combined_filter(self, input_string):
        # Create the array of dictionaries as before
        query_array = self.create_like_query_array(input_string)

        # Encapsulate the array in a dictionary under the $or key
        combined_filter = {"$or": query_array}

        return combined_filter

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        return vector_store.similarity_search(query=query, filter=self.filter, k=self.k)

    def _aget_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        return vector_store.similarity_search(query=query, filter=self.filter, k=self.k)
