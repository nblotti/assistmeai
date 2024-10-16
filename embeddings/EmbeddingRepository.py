import uuid

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embeddings.postgres import vector_store


class EmbeddingRepository:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=200
        )

    def create_embeddings_for_pdf(self, blob_id, perimeter, embeddings_file, file_name):

        docs = self.create_embeddings(embeddings_file)
        for doc in docs:
            doc.metadata = {
                "id": str(uuid.uuid4()),
                "file_name": file_name,
                "blob_id": blob_id,
                "perimeter": perimeter,
                "text": doc.page_content,
                "page": doc.metadata["page"]
            }

        vector_store.add_documents(
            documents=docs,
            ids=[doc.metadata["id"] for doc in docs])

    def create_embeddings(self, embeddings_file):
        loader = PyPDFLoader(embeddings_file)
        return loader.load_and_split(self.text_splitter)

    def delete_all_embeddings(self):
        vector_store.delete_collection()
        vector_store.drop_tables()