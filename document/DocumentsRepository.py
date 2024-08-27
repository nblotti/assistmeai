import os

from psycopg2 import connect, Binary

from document.Document import Document


class DocumentsRepository:
    INSERT_PDF_QUERY = """ INSERT INTO document ( name, owner,perimeter, document)  VALUES ( %s, %s, %s, %s) RETURNING id,created_on;"""

    SELECT_DOCUMENT_QUERY = """SELECT name, document ,owner, perimeter,created_on FROM document WHERE id=%s """

    LIST_PDF_QUERY_BY_USER = """SELECT id::text, name, owner , perimeter,created_on FROM document where owner=%s"""

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
    def save(self, filename, userid, blob_data) -> Document:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_PDF_QUERY,
                       (filename, userid, userid, Binary(blob_data)))

        result = cursor.fetchone()
        generated_id = str(result[0])  # Fetch the first column of the first row
        created_on = result[1]  # Fetch the first column of the first row

        document = Document(id=generated_id, name=filename, owner=userid, perimeter=userid,created_on=created_on)
        conn.commit()
        conn.close()

        return document

    # Function to retrieve blob data from SQLite
    def get_by_id(self, blob_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_DOCUMENT_QUERY, (blob_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def list(self, user):
        """List all documents"""
        conn = self.build_connection()
        cursor = conn.cursor()

        cursor.execute(self.LIST_PDF_QUERY_BY_USER, (user,))
        result = cursor.fetchall()
        conn.close()

        documents = [
            Document(id=row[0], name=row[1], owner=row[2], perimeter=row[3],created_on=row[4])
            for row in result
        ]
        return documents

    def delete_by_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_PDF_QUERY, (blob_id,))
        conn.commit()
        conn.close()

    def delete_embeddings_by_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_EMBEDDING_QUERY, (blob_id,))
        conn.commit()
        conn.close()

    def delete_all(self):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL_QUERY)
        conn.commit()
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
