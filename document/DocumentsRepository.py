import os

from psycopg2 import connect, Binary


class DocumentsRepository:
    INSERT_PDF_QUERY = """ INSERT INTO document ( name, perimeter, document)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_DOCUMENT_QUERY = """SELECT name, document ,perimeter, created_on FROM document WHERE id=%s """

    LIST_PDF_QUERY_BY_USER = """SELECT id, name, perimeter , created_on FROM document where perimeter=%s"""

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
    def save(self, filename, userid, blob_data) -> str:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_PDF_QUERY,
                       (filename, userid, Binary(blob_data)))
        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row

        conn.commit()
        conn.close()

        return str(generated_id)

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
        return result

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
