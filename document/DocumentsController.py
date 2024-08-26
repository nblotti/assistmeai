import io
import os
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import UploadFile, File, APIRouter, Form, Depends, HTTPException
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.para import Paragraph
from starlette.responses import StreamingResponse, Response

from DependencyManager import document_dao_provider
from document.DocumentsRepository import DocumentsRepository
from document.DownloadBlobRequest import DownloadBlobRequest
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
                      owner: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()

    document = documents_repository.save(file.filename, owner, contents)

    temp_file = "./" + document.id + ".document"
    with open(temp_file, "wb") as file_w:
        file_w.write(contents)

    embedding_repository.create_embeddings_for_pdf(document.id, owner, temp_file, file.filename)

    delete_temporary_disk_file(temp_file)

    return document


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
    return documents_repository.list(user)


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


@router_file.post("/web/")
async def download_blob(request: DownloadBlobRequest, documents_repository: document_repository_dep,
                        embedding_repository: embeddings_repository_dep):
    try:
        uuid_str = str(uuid4())
        buffer = io.BytesIO()
        url = request.url
        tags = request.tags
        owner = request.owner
        title = request.title

        # Load and transform documents
        loader = AsyncHtmlLoader(url)
        docs = loader.load()  # Make sure to await asynchronous loader

        bs_transformer = BeautifulSoupTransformer()
        if len(tags) != 0:
            docs_transformed = bs_transformer.transform_documents(docs, tags_to_extract=tags.split(","), remove_lines=False)
        else:
            docs_transformed = bs_transformer.transform_documents(docs)
        # result = chain.invoke({"input": docs_transformed})

        generate_pdf(docs_transformed[0].page_content, buffer)

        # Get the byte data from the buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if len(title) == 0:
            title = uuid_str

        temp_file = f"./{title}.document"

        # Write buffer content to a file on disk
        with open(temp_file, 'wb') as f:
            f.write(pdf_bytes)

        # Save document in repository
        document = documents_repository.save(temp_file, owner, pdf_bytes)

        # Create embeddings
        embedding_repository.create_embeddings_for_pdf(document.id, owner, temp_file, title)

        delete_temporary_disk_file(temp_file)

        return {"status": "success", "uuid": uuid_str, "content": docs_transformed[0].page_content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_pdf(result, buffer):
    # Create a SimpleDocTemplate with the buffer and A4 page size
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Get the sample styles for the paragraphs
    styles = getSampleStyleSheet()
    style = styles['Normal']

    # Create a list to hold the story elements (paragraphs)
    story = []

    # Split the content into paragraphs
    paragraphs = result.split('\n')
    for paragraph in paragraphs:
        # Add each paragraph to the story list
        story.append(Paragraph(paragraph, style))

    # Build the PDF with the story elements
    doc.build(story)
