import datetime


class Conversation:
    id: str
    created_on: datetime
    pdf_id: str
    user_id: int

    def as_dict(self):
        return {
            "id": self.id,
            "pdf_id": self.pdf_id
        }
