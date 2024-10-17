from datetime import date

from numpy import number
from pydantic import BaseModel


class SharedGroupUserCreate(BaseModel):
    group_id: int
    name: str
    creation_date: date
    owner: str
