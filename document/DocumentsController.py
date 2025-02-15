from dataclasses import field
from enum import Enum
from typing import Annotated, List

from fastapi import UploadFile, File, APIRouter, Form, Depends, Query, HTTPException
from fastapi.openapi.models import Response
from fastapi.responses import StreamingResponse
from langchain_core.documents import Document
from pydantic import BaseModel

from ProviderManager import document_manager_provider, shared_group_user_dao_provider, \
    share_group_document_dao_provider, user_manager_provider
from document.Document import DocumentType, DocumentCreate, SharedDocumentCreate, CategoryDocumentCreate, \
    DocumentStatus
from document.DocumentManager import DocumentManager
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.QueryType import QueryType
from rights import UserManager
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
user_manager_dep = Annotated[UserManager, Depends(user_manager_provider)]
shared_group_user_dep = Annotated[SharedGroupUserRepository, Depends(shared_group_user_dao_provider)]
share_group_document_dep = Annotated[SharedGroupDocumentRepository, Depends(share_group_document_dao_provider)]


@router_file.post("/")
async def upload_file(
        document_manager: document_manager_dep,
        owner: str = Form(...),
        document_type: DocumentType = Form(default=DocumentType.DOCUMENT, alias='type'),
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


@router_file.post("/")
async def upload_focus_file(
        document_manager: document_manager_dep,
        owner: str = Form(...),
        document_type: DocumentType = Form(default=DocumentType.DOCUMENT, alias='type'),
        file: UploadFile = File(...)
):

    contents = await file.read()
    return await document_manager.save_focus_document(owner, file.filename, contents, document_type)


@router_file.delete("/{blob_id}/")
def delete(
        document_manager: document_manager_dep,
        blob_id: str):
    rows = document_manager.delete(blob_id)

    return Response(description="Document deleted successfully")


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


@router_file.get("/category/{user}/{category_id}")
async def list_documents(
        user: str,
        category_id: int,
        user_manager: user_manager_dep
) -> List[CategoryDocumentCreate]:
    return await user_manager.list_documents(user, category_id)


class SearchQuery(BaseModel):
    query: str
    ids: List[str] = field(default_factory=list)
    perimeter: str = ""
    k: int = 0


@router_file.post("/search/")
async def list_documents(query: SearchQuery) -> List[Document]:
    k_value = query.k if query.k and query.k != 0 else 10

    if query.perimeter:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, query.perimeter, k_value)
    elif query.ids:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(query.ids), k_value)
    else:
        return []
    return rag_retriever.invoke(query.query)


@router_file.get("/{blob_id}/")
async def download_blob(document_manager: document_manager_dep, blob_id: str):
    document_data: DocumentCreate = document_manager.get_stream_by_id(int(blob_id))

    if document_data:
        # Set headers for the response

        def sanitize_to_latin1(input_str):
            return input_str.encode('latin-1', errors='ignore').decode('latin-1')

        headers = {
            "Content-Disposition": f"attachment; filename={sanitize_to_latin1(document_data.name)}",
            "Content-Type": "application/octet-stream",
            "X-Perimeter": sanitize_to_latin1(document_data.perimeter),
            "X-Owner": sanitize_to_latin1(document_data.owner),
            "X-Created-On": sanitize_to_latin1(document_data.created_on) if document_data.created_on else "",
            "X-File-Name": sanitize_to_latin1(document_data.name),
            "X-Document-Type": sanitize_to_latin1(document_data.document_type),
        }

        def stream_generator():
            yield document_data.document

        # Stream the content
        return StreamingResponse(stream_generator(), media_type="application/octet-stream", headers=headers)
    else:
        raise HTTPException(status_code=404, detail="Blob not found")


@router_file.put("/{blob_id}/status")
async def update_document_status(
        blob_id: str,
        status: DocumentStatus,
        document_manager: document_manager_dep
):
    try:
        document_manager.update_document_status(int(blob_id), status)
        return Response(description="Document status updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FileType(Enum):
    PDF = 'application/pdf'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
