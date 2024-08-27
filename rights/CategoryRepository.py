import os
from typing import Any, List, Tuple

from psycopg2 import connect


class CategoryRepository:
    INSERT_CATEGORY_QUERY = """INSERT INTO document_category (category_name)  VALUES ( %s) RETURNING 
    id;"""

    #SELECT_CATEGORY_QUERY = """SELECT  id,category_name FROM document_category WHERE id=%s """

    #LIST_CATEGORY_QUERY = """SELECT  id, category_name FROM document_category"""

    #LIST_CATEGORY_BY_NAME_QUERY = """SELECT  id, category_name FROM document_category where category_name=%s"""

    #LIST_CATEGORY_BY_IDS = "SELECT  id, category_name FROM document_category where id  IN ({})"

    DELETE_CATEGORY_QUERY = """DELETE FROM document_category WHERE  id = %s"""

    DELETE_ALL_CATEGORY = """DELETE FROM document_category"""

    LIST_ALL_CATEGORY_BY_IDS = """SELECT group_id, category_id, category_name FROM category_by_group WHERE group_id = ANY(%s::text[])"""

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



    def list_by_group_ids(self, group_ids: List[Any]) -> List[Tuple[Any, ...]]:
        """List all documents for the given group IDs"""
        if not group_ids:
            return []

        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_ALL_CATEGORY_BY_IDS, (group_ids,))
        result = cursor.fetchall()
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
