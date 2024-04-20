import os

from fastapi import File, Depends
from embeddings import EmbeddingRepository
from pdf.SqliteDAO import SqliteDAO

db_file = 'pdf.sqlite3'


class PdfManager:
    def __init__(self, embeddingrepository: EmbeddingRepository, sqlitedao: SqliteDAO):
        self.embeddingrepository = embeddingrepository
        self.sqlitedao = sqlitedao

    async def upload_file(self, file: File, user_id : [str], blob_id: str):
        contents = await file.read()

        self.sqlitedao.save(blob_id, file.filename, user_id[0], contents)

        temp_file = "./" + blob_id + ".pdf"
        with open(temp_file, "wb") as file_w:
            file_w.write(contents)

        self.embeddingrepository.create_embeddings_for_pdf(blob_id,user_id, temp_file)

        self.delete_file(temp_file)

        return {"filename": file.filename, "blob_id": blob_id}

    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")

    async def download_blob(self, blob_id: str):
        return self.sqlitedao.get_blob_data_from_sqlite(blob_id)

    async def list_document(self):
        return self.sqlitedao.list()

    async def delete(self, blob_id: str):
        self.embeddingrepository.delete_embeddings_by_file_id(blob_id)
        return self.sqlitedao.delete_by_ids(blob_id)
    async def delete_all(self):
        self.embeddingrepository.delete_all_embeddings()
        self.sqlitedao.delete_all()
