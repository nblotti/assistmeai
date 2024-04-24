from fastapi import UploadFile, File, APIRouter, Depends, Form
from starlette.responses import StreamingResponse, Response

from config import load_config
from chat.InteractionManager import InteractionManager

router_file = APIRouter(
    prefix="/files",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

pdf_manager_provider = load_config()


@router_file.post("/")
async def upload_file(userid: list[str] = Form(...), file: UploadFile = File(...),
                      pdfmanager: InteractionManager = Depends(pdf_manager_provider.get_dependency)):
    blob_id = await pdfmanager.upload_file(file, " ".join(userid))

    return {"filename": file.filename, "blob_id": blob_id}


@router_file.delete("/{blob_id}/")
async def delete(blob_id: str,
                 pdfmanager: InteractionManager = Depends(pdf_manager_provider.get_dependency)):
    pdfmanager.delete(blob_id)
    return Response(status_code=200)


@router_file.get("/{blob_id}/")
async def download_blob(blob_id: str, response: Response,
                        pdfmanager: InteractionManager = Depends(pdf_manager_provider.get_dependency)):
    blob_data = pdfmanager.download_blob(blob_id)

    if blob_data:
        res = blob_data

        # Set headers for the response
        response.headers["Content-Disposition"] = f"attachment; filename={res[0]}"
        response.headers["Content-Type"] = "application/octet-stream"

        return StreamingResponse(iter([bytes(res[1])]), media_type="application/files")
        # Stream the content
    else:
        return {"error": "Blob not found"}


@router_file.get("/")
async def list_document(pdfmanager: InteractionManager = Depends(pdf_manager_provider.get_dependency)):
    return pdfmanager.list_document()


@router_file.delete("/")
async def delete_all(pdfmanager: InteractionManager = Depends(pdf_manager_provider.get_dependency)):
    pdfmanager.delete_all()
    return Response(status_code=200)
