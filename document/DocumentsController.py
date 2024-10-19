from enum import Enum
from typing import Annotated, List

from fastapi import UploadFile, File, APIRouter, Form, Depends, Query, HTTPException
from starlette.responses import StreamingResponse, Response

from ProviderManager import document_manager_provider, shared_group_user_dao_provider, share_group_document_dao_provider
from document.Document import DocumentType, DocumentCreate, SharedDocumentCreate
from document.DocumentManager import DocumentManager
from sharing.SharedGroupDocument import SharedGroupDocumentCreate
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupUser import SharedGroupUserCreate
from sharing.SharedGroupUserRepository import SharedGroupUserRepository

router_file = APIRouter(
    prefix="/document",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]
shared_group_user_dep = Annotated[SharedGroupUserRepository, Depends(shared_group_user_dao_provider)]
share_group_document_dep = Annotated[SharedGroupDocumentRepository, Depends(share_group_document_dao_provider)]


@router_file.post("/")
async def upload_file(
        document_manager: document_manager_dep,
        owner: str = Form(...),
        document_type: DocumentType = Form(DocumentType.DOCUMENT, alias='type'),
        file: UploadFile = File(...)
):
    enum_type = FileType.PDF

    contents = await file.read()

    if file.filename.endswith(".pdf"):
        enum_type = FileType.PDF
    elif file.filename.endswith(".docx"):
        enum_type = FileType.DOCX
    elif file.filename.endswith(".xlsx"):
        enum_type = FileType.XLSX
    elif file.filename.endswith(".pptx"):
        enum_type = FileType.PPTX
    else:
        raise ValueError("Unsupported file type")

    if enum_type == FileType.DOCX:
        return await document_manager.convert_and_upload_file(owner, file.filename, contents, document_type)
    else:
        # Upload file
        return await document_manager.upload_file(owner, file.filename, contents, document_type)


@router_file.delete("/{blob_id}/")
def delete(
        document_manager: document_manager_dep,
        blob_id: str):
    rows = document_manager.delete(blob_id)

    return Response(status_code=200)


@router_file.get("/user/{user}")
async def list_documents(
        user: str,
        document_manager: document_manager_dep,
        document_type: DocumentType = Query(DocumentType.DOCUMENT, alias='type'),

):
    documents = document_manager.list_documents_by_type(user, document_type=document_type)
    if not documents:
        return []
    return documents


@router_file.get("/shared/{user}")
async def list_documents(
        user: str,
        document_manager: document_manager_dep,
        shared_group_user_repository: shared_group_user_dep,
        shared_group_document_repository: share_group_document_dep

):
    shared_document_groups: List[SharedGroupDocumentCreate] = []
    documents: List[SharedDocumentCreate] = []

    user_groups: List[SharedGroupUserCreate] = shared_group_user_repository.list_by_user_id(user)

    for user_group in user_groups:
        shared_document_group: List[SharedGroupDocumentCreate] = shared_group_document_repository.list_by_group_id(
            int(user_group.group_id))
        shared_document_groups.extend(shared_document_group)

    for document_group in shared_document_groups:
        document = document_manager.get_by_id(int(document_group.document_id))
        shared_document = SharedDocumentCreate(**document.model_dump())
        shared_document.shared_group_id = document_group.group_id
        documents.append(shared_document)
    return documents


@router_file.get("/{blob_id}/")
async def download_blob(document_manager: document_manager_dep, blob_id: str, response: Response):
    document_data: DocumentCreate = document_manager.get_stream_by_id(int(blob_id))

    if document_data:
        # Set headers for the response
        response.headers["Content-Disposition"] = f"attachment; filename={document_data.name}"
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["X-Perimeter"] = document_data.perimeter
        response.headers["X-Created-On"] = document_data.created_on if document_data.created_on else ""

        def stream_generator():
            yield document_data.document

        # Stream the content
        return StreamingResponse(stream_generator(), media_type="application/object")
    else:
        raise HTTPException(status_code=404, detail="Blob not found")


class FileType(Enum):
    PDF = 'application/pdf'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
