from typing import Sequence

from sqlalchemy import and_, select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from BaseAlchemyRepository import BaseAlchemyRepository
from document.Document import Document, DocumentType, DocumentCreate, DocumentStatus


class DocumentsRepository(BaseAlchemyRepository):
    SELECT_DOCUMENT_STREAM_QUERY = """SELECT * FROM document WHERE id=%s """

    # Function to store blob data in SQLite
    def save(self, document: DocumentCreate) -> DocumentCreate:

        try:
            new_document = Document(
                name=document.name,
                perimeter=document.perimeter,
                owner=document.owner,
                document_type=document.document_type,
                document=document.document,  # Saving the binary content
                document_status=document.document_status,
                focus_only=document.focus_only
            )

            self.db.add(new_document)
            self.db.commit()
            self.db.refresh(new_document)
            self.db.close()
            document.id = str(new_document.id)
            document.document = None
            return document
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    def update_document_status(self, document_id: int, new_status: DocumentStatus):
        """
        Update the status of a document.
        :param document_id: The ID of the document to update.
        :param new_status: The new status to set.
        :return: True if the update was successful, False otherwise.
        """
        try:
            stmt = (
                select(Document)
                .where(Document.id == document_id)
            )
            document: Document = self.db.execute(stmt).scalars().first()

            if not document:
                return False

            document.document_status = new_status
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            return False
        finally:
            self.db.close()

    def get_by_id(self, blob_id: int) -> DocumentCreate:

        stmt = select(Document).where(Document.id == blob_id)
        document: Document = self.db.execute(stmt).scalars().first()

        return self.map_to_document(document)

    def get_document_by_id(self, blob_id: int) -> DocumentCreate:
        with Session(self.db.connection()) as session:
            try:
                stmt = select(Document).where(Document.id == blob_id)
                result = session.execute(stmt).scalars().first()

                if not result:
                    return None

                return DocumentCreate(
                    id=str(result.id),
                    name=result.name,
                    created_on=result.created_on.strftime("%d.%m.%Y"),
                    perimeter=result.perimeter,
                    document=result.document,
                    owner=result.owner,
                    summary_id=result.summary_id,
                    summary_status=result.summary_status,
                    document_type=result.document_type,
                    document_status=result.document_status,
                    focus_only=result.focus_only
                )
            except SQLAlchemyError as e:
                print(f"Database error occurred: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

    def list_by_type(self, user: str, document_type: DocumentType):
        """List all documents"""

        if document_type == DocumentType.ALL:
            stmt = select(Document).where(Document.owner == user)
        else:
            stmt = select(Document).where(and_(Document.owner == user,
                                               Document.document_type == document_type))
        documents: Sequence[Document] = self.db.execute(stmt).scalars().all()

        return [self.map_to_document(doc) for doc in documents]

    def delete_by_id(self, blob_id: int):
        stmt = delete(Document).where(Document.id == blob_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def map_to_document(self, document: Document) -> DocumentCreate:

        return DocumentCreate(
            id=str(document.id),
            name=document.name,
            owner=document.owner,
            perimeter=document.perimeter,
            created_on=document.created_on.strftime("%d.%m.%Y"),
            summary_id=document.summary_id,
            summary_status=document.summary_status,
            document_type=document.document_type,
            document_status=document.document_status,
            focus_only=document.focus_only
        )
