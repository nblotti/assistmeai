from typing import List

from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from document.Document import Document, DocumentType, DocumentCreate


class DocumentsRepository(BaseAlchemyRepository):
    DELETE_EMBEDDING_QUERY = """DELETE FROM langchain_pg_embedding WHERE cmetadata ->>'blob_id' =%s;"""

    GET_EMBEDDING_QUERY = """SELECT cmetadata ->>'text' FROM langchain_pg_embedding 
    WHERE cmetadata ->>'blob_id' in %s;"""

    # Function to store blob data in SQLite
    def save(self, document: DocumentCreate) -> DocumentCreate:

        try:
            new_document = Document(
                name=document.name,
                perimeter=document.perimeter,
                owner=document.owner,
                document=document.document  # Saving the binary content
            )

            self.db.add(new_document)
            self.db.commit()
            self.db.refresh(new_document)
            self.db.close()
            document.id = new_document.id
            return document
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    def get_by_id(self, blob_id):

        documents: List[Document] = self.db.query(Document).filter(Document.id == blob_id).all()

        return [self.map_to_document(doc) for doc in documents]

    def get_document_by_id(self, blob_id) -> DocumentCreate:
        conn = self.db.connection().connection  # Access the raw DB connection from the session
        cursor = conn.cursor()  # Direct access to the cursor

        try:
            cursor.execute(self.SELECT_DOCUMENT_STREAM_QUERY, (blob_id,))
            result = cursor.fetchone()
            if not result:
                return None
            return DocumentCreate(
                id=result[0],
                name=result[1],
                created_on=result[2],
                perimeter=result[3],
                document=result[4],
                owner=result[5],
                summary_id=result[6],
                summary_status=result[7],
                document_type=result[8])
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    def list_by_type(self, user, document_type: DocumentType):
        """List all documents"""

        if document_type == DocumentType.ALL:
            documents: List[Document] = self.db.query(Document).filter(Document.owner == user).all()
        else:
            documents: List[Document] = self.db.query(Document).filter(Document.document_type == document_type).all()

        return [self.map_to_document(doc) for doc in documents]

    def delete_by_id(self, blob_id: str):

        affected_rows = self.db.query(Document).filter(Document.id == blob_id).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def map_to_document(self, document: Document) -> DocumentCreate:
        """
        :param assistant_document: AssistantsDocument object to be converted.
        :return: AssistantsDocumentList object containing the mapped values.
        """
        return DocumentCreate(
            id=Document.id,
            name=Document.name,
            owner=Document.owner,
            perimeter=Document.perimeter,
            created_on=Document.created_on,
            summary_id=Document.summary_id,
            summary_status=Document.summary_status,
            document_type=Document.document_type
        )
