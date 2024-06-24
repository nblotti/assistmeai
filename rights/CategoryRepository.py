import os
from typing import Any

from psycopg2 import connect


class CategoryRepository:
    INSERT_CATEGORY_QUERY = """INSERT INTO document_category (category_name)  VALUES ( %s) RETURNING 
    id;"""

    SELECT_CATEGORY_QUERY = """SELECT  id,category_name FROM document_category WHERE id=%s """

    LIST_CATEGORY_QUERY = """SELECT  id, category_name FROM document_category"""

    LIST_CATEGORY_BY_NAME_QUERY = """SELECT  id, category_name FROM document_category where category_name=%s"""

    LIST_CATEGORY_BY_IDS = "SELECT  id, category_name FROM document_category where id  IN ({})"

    DELETE_CATEGORY_QUERY = """DELETE FROM document_category WHERE  id = %s"""

    DELETE_ALL_CATEGORY = """DELETE FROM document_category"""

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
    def save(self, category_name) -> str:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_CATEGORY_QUERY, category_name)
        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row

        conn.commit()
        conn.close()

        return str(generated_id)

    # Function to retrieve blob data from SQLite
    def get_by_ids(self, category_ids):
        conn = self.build_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(category_ids))
        # Construct the SQL query with the correct placeholders
        query = self.LIST_CATEGORY_BY_IDS.format(placeholders)

        # Execute the query with the list of group_ids as parameters
        cursor.execute(query, tuple(category_ids))
        result = cursor.fetchall()
        conn.close()
        return result if result else None

    def get_by_id(self, category_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_CATEGORY_QUERY, category_id)
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def list(self) -> list[tuple[Any, ...]]:
        """List all documents"""
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_CATEGORY_QUERY)
        result = cursor.fetchall()
        conn.close()
        return result

    def list_by_name(self, name: str) -> tuple[Any, ...]:
        """List all documents"""
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_CATEGORY_BY_NAME_QUERY, [name])
        result = cursor.fetchone()
        conn.close()
        return result

    def delete_by_id(self, category_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CATEGORY_QUERY, (category_id,))
        conn.commit()
        conn.close()

    def delete_all(self):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL_CATEGORY)
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
