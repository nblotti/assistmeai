from psycopg2 import connect, Binary


class DocumentsRepository:
    INSERT_PDF = """ INSERT INTO document ( name, perimeter, document)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_DOCUMENT = """SELECT name, document , created_on FROM document WHERE id=%s """

    LIST_PDF = """SELECT id, name, perimeter , created_on FROM document"""

    DELETE_PDF = """DELETE FROM document WHERE id = %s"""

    DELETE_ALL = """DELETE FROM document"""

    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, db_name: str, db_host: str, db_port: str, db_user: str, db_password: str):
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password


    # Function to store blob data in SQLite
    def save(self, filename, userid, blob_data) -> str:
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_PDF,
                       (filename, userid, Binary(blob_data)))
        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row

        conn.commit()
        conn.close()

        return str(generated_id)

    # Function to retrieve blob data from SQLite
    def get_by_id(self, blob_id):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_DOCUMENT, (blob_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def list(self) -> str:
        """List all documents"""
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_PDF)
        result = cursor.fetchall()
        conn.close()
        return result

    def delete_by_id(self, blob_ids: str):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_PDF, (blob_ids,))
        conn.commit()
        conn.close()

    def delete_all(self):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL)
        conn.commit()
        conn.close()

    def buildConnection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn


