from enum import Enum
from typing import Annotated, Optional

from fastapi import UploadFile, File, APIRouter, Form, Depends, Query
from starlette.responses import StreamingResponse, Response

from ProviderManager import document_manager_provider
from document.Document import DocumentType
from document.DocumentManager import DocumentManager

router_file = APIRouter(
    prefix="/document",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider.get_dependency)]


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
    document_manager.delete(blob_id)

    return Response(status_code=200)


@router_file.delete("/")
async def delete_all(
        document_manager: document_manager_dep
):
    document_manager.delete_all()
    document_manager.delete_all()

    return Response(status_code=200)


@router_file.get("/")
async def list_document(document_manager: document_manager_dep, user: Optional[str] = None):
    if user is None:
        return Response(status_code=404)
    return document_manager.list_documents(user)


@router_file.get("/users/{user}/documents")
async def list_documents(
        user: str,
        document_manager: document_manager_dep,
        document_type: DocumentType = Query(DocumentType.DOCUMENT, alias='type'),

):
    documents = document_manager.list_documents_by_type(user, document_type=document_type)
    if not documents:
        return []
    return documents


@router_file.get("/{blob_id}/")
async def download_blob(document_manager: document_manager_dep, blob_id: str,
                        response: Response):
    blob_data = document_manager.get_stream_by_id(blob_id)

    if blob_data:
        res = blob_data

        # Set headers for the response
        response.headers["Content-Disposition"] = f"attachment; filename={res[0]}"
        response.headers["Content-Type"] = "application/octet-stream"

        return StreamingResponse(iter([bytes(res[1])]), media_type="application/document")
        # Stream the content
    else:
        return {"error": "Blob not found"}


class FileType(Enum):
    PDF = 'application/pdf'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
