import json
import sqlite3


class SqliteDAO:
    INSERT_PDF = "INSERT INTO files (id, name, userid, document) VALUES (?, ?, ?,? )"
    SELECT_DOCUMENT = "SELECT name, document FROM files WHERE id=?"
    LIST_PDF = "SELECT id, name, userid FROM files"
    DELETE_PDF = "DELETE FROM files where id = ?"
    DELETE_ALL= "DELETE FROM files;"

    def __init__(self):
        conn = sqlite3.connect('files.sqlite3')

    # Function to store blob data in SQLite
    def save(self, blob_id,filename, userid, blob_data):
        conn = sqlite3.connect('files.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.INSERT_PDF,
                       (blob_id, filename, userid, sqlite3.Binary(blob_data)))
        conn.commit()
        conn.close()

    # Function to retrieve blob data from SQLite
    def get_by_id(self, blob_id):
        conn = sqlite3.connect('files.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.SELECT_DOCUMENT, (blob_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def list(self) -> str:
        """List all documents"""
        conn = sqlite3.connect('files.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.LIST_PDF)
        result = cursor.fetchall()
        conn.close()
        return json.dumps(result)

    def delete_by_ids(self, blob_ids: str):
        conn = sqlite3.connect('files.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.DELETE_PDF, (blob_ids,))
        conn.commit()
        conn.close()
    def delete_all(self):
        conn = sqlite3.connect('files.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL)
        conn.commit()
        conn.close()
