from typing import List, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from document.DocumentCategory import DocumentCategoryCreate, DocumentCategory, DocumentCategoryByGroup, \
    DocumentCategoryByGroupCreate


class DocumentCategoryRepository(BaseAlchemyRepository):

    # Function to store blob data in SQLite
    def save(self, category: DocumentCategoryCreate) -> DocumentCategoryCreate:

        try:
            new_category = DocumentCategory(
                category_name=category.name,
            )

            self.db.add(new_category)
            self.db.commit()
            self.db.refresh(new_category)
            self.db.close()
            category.id = str(new_category.id)
            return category
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    def list_by_group_ids(self, group_ids: List[str]) -> List[DocumentCategoryByGroupCreate]:
        """List all documents for the given group IDs"""
        if not group_ids:
            return []
        stmt = select(DocumentCategoryByGroup).where(DocumentCategoryByGroup.group_id.in_(group_ids))
        documents: Sequence[DocumentCategoryByGroup] = self.db.execute(stmt).scalars().all()

        return [self.map_to_document_category_by_group(doc) for doc in documents]

    def delete_by_id(self, category_id: str):

        stmt = delete(DocumentCategoryByGroup).where(DocumentCategory.id == category_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows

    def map_to_document_category_by_group(self, document: DocumentCategoryByGroup) -> DocumentCategoryByGroupCreate:

        return DocumentCategoryByGroupCreate(
            group_id=document.group_id,
            category_id=document.category_id,
            category_name=document.category_name,
            enabled=True
        )
