import os

from psycopg2 import connect, Binary, DatabaseError

from document.Document import Document, DocumentType, Jobstatus


class DocumentsRepository:
    INSERT_PDF_QUERY = """ INSERT INTO document ( name, owner,perimeter, document, document_type)  VALUES ( %s, %s, %s, %s, %s) RETURNING id,created_on;"""

    SELECT_DOCUMENT_QUERY = """SELECT name, document ,owner, perimeter,created_on, document_type, summary_id, summary_status FROM document WHERE id=%s """

    LIST_PDF_QUERY_BY_USER_AND_TYPE = """SELECT id::text, name, owner , perimeter,created_on,summary_id, summary_status FROM document 
    where owner=%s and document_type=%s"""

    DELETE_PDF_QUERY = """DELETE FROM document WHERE id = %s"""

    DELETE_ALL_QUERY = """DELETE FROM document"""

    DELETE_EMBEDDING_QUERY = """DELETE FROM langchain_pg_embedding WHERE cmetadata ->>'blob_id' =%s;"""

    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, ):
        self.db_name = os.getenv("DB_NAME")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")

    # Function to store blob data in SQLite
    def save(self, filename, userid, blob_data, document_type) -> Document:
        conn = None
        cursor = None
        try:
            conn = self.build_connection()
            cursor = conn.cursor()
            cursor.execute(self.INSERT_PDF_QUERY,
                           (filename, userid, userid, Binary(blob_data), document_type))

            result = cursor.fetchone()
            generated_id = str(result[0])  # Fetch the first column of the first row
            created_on = result[1]  # Fetch the first column of the first row

            document = Document(id=generated_id,
                                name=filename,
                                owner=userid,
                                perimeter=userid,
                                created_on=created_on,
                                document_type=document_type)

            conn.commit()
            return document
        except DatabaseError as e:
            print(f"Database error occurred: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_by_id(self, blob_id):
        conn = None
        cursor = None
        try:
            conn = self.build_connection()
            cursor = conn.cursor()
            cursor.execute(self.SELECT_DOCUMENT_QUERY, (blob_id,))
            result = cursor.fetchone()

            if result:
                document = Document(id=result[0],
                                    name=result[1],
                                    owner=result[2],
                                    perimeter=result[3],
                                    created_on=result[4],
                                    document_type=DocumentType(result[5]),
                                    summary_id=result[6],
                                    summary_status=Jobstatus(result[7]))
                return document
            else:
                return None
        except DatabaseError as e:
            print(f"Database error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list(self, user, document_type: DocumentType):
        """List all documents"""
        conn = None
        cursor = None
        documents = []
        try:
            conn = self.build_connection()
            cursor = conn.cursor()

            cursor.execute(self.LIST_PDF_QUERY_BY_USER_AND_TYPE, (user, document_type))
            result = cursor.fetchall()

            documents = [
                Document(id=row[0],
                         name=row[1],
                         owner=row[2],
                         perimeter=row[3],
                         created_on=row[4],
                         document_type=document_type,
                         summary_id=row[5],
                         summary_status=Jobstatus(row[6]))
                for row in result
            ]
        except DatabaseError as e:
            print(f"Database error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return documents

    def delete_by_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_PDF_QUERY, (blob_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def delete_embeddings_by_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_EMBEDDING_QUERY, (blob_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def delete_all(self):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL_QUERY)
        conn.commit()
        cursor.close()
        conn.close()

    def build_connection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn
