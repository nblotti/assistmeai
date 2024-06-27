import json
import os
from typing import Annotated, Optional

from fastapi import UploadFile, File, APIRouter, Form, Depends
from starlette.responses import StreamingResponse, Response

from CustomEncoder import CustomEncoder
from DependencyManager import document_dao_provider

from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository

router_file = APIRouter(
    prefix="/document",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

document_repository_dep = Annotated[DocumentsRepository, Depends(document_dao_provider.get_dependency)]
embeddings_repository_dep = Annotated[EmbeddingRepository, Depends(EmbeddingRepository)]


@router_file.post("/")
async def upload_file(documents_repository: document_repository_dep,
                      embedding_repository: embeddings_repository_dep,
                      perimeter: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()

    blob_id = documents_repository.save(file.filename, perimeter, contents)

    temp_file = "./" + blob_id + ".document"
    with open(temp_file, "wb") as file_w:
        file_w.write(contents)

    embedding_repository.create_embeddings_for_pdf(blob_id, perimeter, temp_file, file.filename)

    delete_temporary_disk_file(temp_file)

    return {"filename": file.filename, "blob_id": blob_id}


'''
    This method deletes a temporary file on the HD
'''


def delete_temporary_disk_file(file_path):
    try:
        os.remove(file_path)
        print(f"File '{file_path}' deleted successfully.")
    except OSError as e:
        print(f"Error deleting file '{file_path}': {e}")


@router_file.delete("/{blob_id}/")
def delete(
        documents_repository: document_repository_dep,
        blob_id: str):
    documents_repository.delete_by_id(blob_id)
    return Response(status_code=200)


@router_file.delete("/")
async def delete_all(
        documents_repository: document_repository_dep,
        embedding_repository: embeddings_repository_dep
):
    documents_repository.delete_all()
    embedding_repository.delete_all_embeddings()

    return Response(status_code=200)


@router_file.get("/")
async def list_document(documents_repository: document_repository_dep, user: Optional[str] = None):

    if user is None:
        return Response(status_code=404)
    return json.loads(json.dumps(documents_repository.list(user), cls=CustomEncoder))


@router_file.get("/{blob_id}/")
async def download_blob(documents_repository: document_repository_dep, blob_id: str,
                        response: Response):
    blob_data = documents_repository.get_by_id(blob_id)

    if blob_data:
        res = blob_data

        # Set headers for the response
        response.headers["Content-Disposition"] = f"attachment; filename={res[0]}"
        response.headers["Content-Type"] = "application/octet-stream"

        return StreamingResponse(iter([bytes(res[1])]), media_type="application/document")
        # Stream the content
    else:
        return {"error": "Blob not found"}
