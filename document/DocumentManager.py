import os
import subprocess
import uuid

from document.Document import DocumentType
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository


class DocumentManager:

    def __init__(self, document_repository: DocumentsRepository, embedding_repository: EmbeddingRepository):
        self.document_repository = document_repository
        self.embedding_repository = embedding_repository

    async def convert_and_upload_file(self, owner: str, filename: str, contents: bytes,
                                      document_type: DocumentType = DocumentType.DOCUMENT):

        path = "./" + str(uuid.uuid4())
        temp_file = path + ".docx"
        temp_pdf_file = path + ".pdf"

        with open(temp_file, "wb") as file_w:
            file_w.write(contents)

        binary_content = subprocess.check_output(['libreoffice', '--headless', '--convert-to', 'pdf', temp_file])

        # Read the PDF file in binary mode
        with open(temp_pdf_file, 'rb') as file:
            binary_content = file.read()

        self.delete_temporary_disk_file(temp_file)
        self.delete_temporary_disk_file(temp_pdf_file)

        file_name_pdf_extension = filename[:-5] + ".pdf"  # Remove last 5 characters (".docx")

        return await self.upload_file(owner, file_name_pdf_extension, binary_content, document_type)

    async def upload_file(self, owner: str, filename: str, contents: bytes,
                          document_type: DocumentType = DocumentType.DOCUMENT):

        file_name_pdf_extension = filename[:-4]  # Remove last 5 characters (".docx")
        document = self.document_repository.save(file_name_pdf_extension, owner, contents, document_type)

        temp_file = "./" + document.id + ".document"
        with open(temp_file, "wb") as file_w:
            file_w.write(contents)

        self.embedding_repository.create_embeddings_for_pdf(document.id, owner, temp_file, file_name_pdf_extension)

        self.delete_temporary_disk_file(temp_file)

        return document

    '''
        This method deletes a temporary file on the HD
    '''

    def delete_temporary_disk_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")

    def delete(self, blob_id: str):
        self.document_repository.delete_by_id(blob_id)

    def delete_all(self):
        self.document_repository.delete_all()
        self.embedding_repository.delete_all_embeddings()

    def list_documents(self, user: str):
        return self.list_documents_by_type(user, DocumentType.DOCUMENT)

    def list_documents_by_type(self, user: str, document_type: DocumentType):
        return self.document_repository.list_no_content(user, document_type)

    def get_by_id(self, blob_id: str, ):
        return self.document_repository.get_by_id_no_content(blob_id)

    def get_stream_by_id(self, blob_id: str):
        return self.document_repository.get_stream_by_id(blob_id)

    def delete_embeddings_by_id(self, blob_id):
        return self.document_repository.delete_embeddings_by_id(blob_id)

    def create_embeddings_for_pdf(self, blob_id, new_perimeter, temp_file, name):
        return self.embedding_repository.create_embeddings_for_pdf(blob_id, new_perimeter, temp_file, name)
