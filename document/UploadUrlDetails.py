from pydantic import BaseModel


class UploadUrlDetails(BaseModel):
    url: str
    tags: str
    owner: str
    title: str
