from sqlalchemy.orm import Session


class BaseAlchemyRepository:

    def __init__(self, db: Session):
        self.db = db