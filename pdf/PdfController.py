import uuid

from fastapi import UploadFile, File, APIRouter, Depends, Form

from DependencyManager import PdfManagerProvider, EmbeddingRepositoryProvider, SqliteDAOProvider
from config import load_config
from pdf.PdfManager import PdfManager

db_file = 'pdf.sqlite3'

router_file = APIRouter(
    prefix="/files",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

load_config()

# Create instances of dependency providers
embedding_repository_provider = EmbeddingRepositoryProvider()
sqlite_dao_provider = SqliteDAOProvider()

pdf_manager_provider = PdfManagerProvider(embedding_repository_provider, sqlite_dao_provider)


@router_file.post("/")
async def upload_file(userid:list[str] = Form(...), file: UploadFile = File(...),
                      pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    blob_id = str(uuid.uuid4())
    await pdfmanager.upload_file(file, userid,blob_id)

    return {"filename": file.filename, "blob_id": blob_id}


def delete_file(file_path,
                pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    pdfmanager.delete_file(file_path)


@router_file.get("/list")
async def list_document(pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    return await pdfmanager.list_document()


@router_file.delete("/")
async def delete(blob_id: str,
                 pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    return await pdfmanager.delete(blob_id)


@router_file.get("/{blob_id}")
async def download_blob(blob_id: str,
                        pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    return await pdfmanager.download_blob(blob_id)


@router_file.delete("/all")
async def delete(pdfmanager: PdfManager = Depends(pdf_manager_provider.get_dependency)):
    return await pdfmanager.delete_all()
