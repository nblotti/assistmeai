from pydantic import BaseModel


class DownloadBlobRequest(BaseModel):
    url: str
    url: str
    tags: str
    owner: str
    title: str
