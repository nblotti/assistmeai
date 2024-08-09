import json
from typing import List, Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from embeddings.EmbeddingsTools import QueryType
from vector_stores.postgres import vector_store


class CustomAzurePGVectorRetriever(BaseRetriever):
    filter: dict = {}


    def __init__(self, query_type: QueryType, value: str, **kwargs: Any):
        super().__init__(**kwargs)

        if query_type == QueryType.DOCUMENT:
            self.filter = {'blob_id': {"$eq": value}}
        else:
            self.filter = {'perimeter': {"$in": json.loads(json.dumps(value.split()))}}

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        return vector_store.similarity_search(query=query, filter=self.filter)

    def _aget_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        return vector_store.similarity_search(query=query, filter=self.filter)
