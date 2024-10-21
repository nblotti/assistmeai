from typing import Sequence, List

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from sharing.SharedGroupDocument import SharedGroupDocument, SharedGroupDocumentCreate


class SharedGroupDocumentRepository(BaseAlchemyRepository):

    def create(self, group: SharedGroupDocumentCreate) -> SharedGroupDocumentCreate:

        try:
            new_group = SharedGroupDocument(
                group_id=group.group_id,
                document_id=group.document_id,
            )

            self.db.add(new_group)
            self.db.commit()
            self.db.refresh(new_group)
            self.db.close()
            group.id = str(new_group.id)
            group.creation_date = new_group.creation_date.strftime("%d.%m.%Y")
            return group
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    def read(self, id) -> SharedGroupDocumentCreate:
        stmt = select(SharedGroupDocument).where(SharedGroupDocument.id == id)
        document: SharedGroupDocument = self.db.execute(stmt).scalars().first()

        return self.map_to_share_group_document(document)

    def delete(self, group_id:int):
        stmt = delete(SharedGroupDocument).where(SharedGroupDocument.id == group_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def list_by_group_id(self, group_id:int) -> List[SharedGroupDocumentCreate]:
        stmt = select(SharedGroupDocument).where(SharedGroupDocument.group_id == group_id)
        documents: Sequence[SharedGroupDocument] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[SharedGroupDocumentCreate] = [
            self.map_to_share_group_document(row)
            for row in documents
        ]
        return groups

    def list_by_document_id(self, document_id:int) -> List[SharedGroupDocumentCreate]:
        stmt = select(SharedGroupDocument).where(SharedGroupDocument.document_id == document_id)
        documents: Sequence[SharedGroupDocument] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[SharedGroupDocumentCreate] = [
            self.map_to_share_group_document(row)
            for row in documents
        ]
        return groups

    def map_to_share_group_document(self, document: SharedGroupDocument) -> SharedGroupDocumentCreate:
        return SharedGroupDocumentCreate(
            id=str(document.id),
            group_id=str(document.group_id),
            document_id=str(document.document_id),
            creation_date=document.creation_date.strftime("%d.%m.%Y")
        )
