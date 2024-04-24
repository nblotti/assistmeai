import os

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from vector_stores.pinecone import vector_store, pc


class EmbeddingRepository:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=200
        )

    def create_embeddings_for_pdf(self, blob_id, user_id, embeddings_file):
        loader = PyPDFLoader(embeddings_file)
        docs = loader.load_and_split(self.text_splitter)

        for doc in docs:
            doc.metadata = {
                "blob_id": blob_id,
                "user_id": user_id,
                "text": doc.page_content,
                "page": doc.metadata["page"]
            }
        vector_store.add_documents(docs)

    def delete_embeddings_by_file_id(self, blob_id):
        pass

    def delete_all_embeddings(self):
        index_name = os.getenv("PINECONE_INDEX_NAME")
        index = pc.Index(index_name)
        index.delete(delete_all=True)

