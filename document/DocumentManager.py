import os

from document.Document import DocumentType, DocumentCreate, DocumentStatus
from document.DocumentsRepository import DocumentsRepository


class DocumentManager:

    def __init__(self, document_repository: DocumentsRepository):
        self.document_repository = document_repository

    async def upload_file(self, owner: str, filename: str, contents: bytes,
                          document_type: DocumentType = DocumentType.DOCUMENT, ):

        if not filename.endswith("pdf"):
            focus_only = True
        else:
            focus_only = False

        new_document = DocumentCreate(
            owner=owner,
            name=filename,
            perimeter=owner,
            document=contents,
            document_type=document_type,
            focus_only=focus_only
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

    def update_document_status(self, document_id: int, status: DocumentStatus) -> None:
        return self.document_repository.update_document_status(document_id, status)
