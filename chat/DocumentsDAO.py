import json
from datetime import datetime

from psycopg2 import connect, Binary

import config


class DocumentsDAO:
    INSERT_PDF = """ INSERT INTO pdf ( name, userid, document)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_DOCUMENT = """SELECT name, document , created_on FROM pdf WHERE id=%s """

    LIST_PDF = """SELECT id, name, userid , created_on FROM pdf"""

    DELETE_PDF = """DELETE FROM pdf WHERE id = %s"""

    DELETE_ALL = """DELETE FROM pdf"""

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
        return json.dumps(result, cls=CustomEncoder)

    def delete_by_ids(self, blob_ids: str):
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


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%d.%m.%Y")  # Convert datetime object to string in "dd.MM.YYYY" format
        return json.JSONEncoder.default(self, obj)
