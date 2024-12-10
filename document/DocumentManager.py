import os
import subprocess
import uuid

from httpx import AsyncClient

from document.Document import DocumentType, DocumentCreate, DocumentStatus
from document.DocumentsRepository import DocumentsRepository
from embeddings.DocumentsEmbeddingsRepository import DocumentsEmbeddingsRepository
from job.Job import JobCreate, JobType
from job.JobRepository import JobRepository


class DocumentManager:

    def __init__(self, document_embeddings_repository: DocumentsEmbeddingsRepository,
                 document_repository: DocumentsRepository):
        self.document_repository = document_repository
        self.document_embeddings_repository = document_embeddings_repository

    async def convert_and_upload_file(self, owner: str, filename: str, contents: bytes,
                                      document_type: DocumentType = DocumentType.DOCUMENT):

        path = "./" + str(uuid.uuid4())
        temp_file = path + ".document"
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

        new_document = DocumentCreate(
            owner=owner,
            name=filename,
            perimeter=owner,
            document=contents,
            document_type=document_type
        )

        return self.document_repository.save(new_document)

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
        return self.document_repository.delete_by_id(int(blob_id))

    def list_documents(self, user: str):
        return self.list_documents_by_type(user, DocumentType.DOCUMENT)

    def list_documents_by_type(self, user: str, document_type: DocumentType):
        return self.document_repository.list_by_type(user, document_type)

    def get_by_id(self, blob_id: int, ) -> DocumentCreate:
        return self.document_repository.get_by_id(blob_id)

    def get_stream_by_id(self, blob_id: int) -> DocumentCreate:
        return self.document_repository.get_document_by_id(blob_id)

    def delete_embeddings_by_id(self, blob_id):
        return self.document_embeddings_repository.delete_embeddings_by_id(blob_id)

    def update_document_status(self, document_id: int, status: DocumentStatus) -> None:
        return self.document_repository.update_document_status(document_id, status)

    def get_embeddings_by_ids(self, blob_ids: [str]):
        return self.document_embeddings_repository.get_embeddings_by_ids(blob_ids)

    async def start_async_job(self, blob_id: str, perimeter: str):
        url = os.environ["LONG_EMBEDDINGS_SCRATCH_URL"]

        job = JobCreate(
            source=blob_id,
            owner=perimeter,
            job_type=JobType.LONG_EMBEDDINGS
        )

        async with AsyncClient(timeout=30) as client:
            response = await client.post(url, json=job.model_dump())

        if response.status_code != 200:
            print(f"Error creating embedding job for long document with id {blob_id}: \n{response.text}")
