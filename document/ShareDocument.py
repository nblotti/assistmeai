from pydantic import BaseModel


class ShareDocument(BaseModel):
    document_id: str
    share_group_id: str
    perimeter_change: str
    type_of_change: str
