import os
from typing import List, Tuple, Any

from psycopg2 import connect


class UserRepository:
    INSERT_GROUP_QUERY = """ INSERT INTO user_groups ( group_id, category_id)  VALUES ( %s, %s) RETURNING id;"""

    SELECT_GROUP_QUERY = """SELECT id,group_id, category_id FROM user_groups WHERE id=%s """

    LIST_GROUP_QUERY = """SELECT id, group_id, category_id FROM user_groups"""

    LIST_CATEGORY_FOR_GROUP_QUERY = "SELECT * FROM user_groups WHERE group_id IN ({})"

    DELETE_GROUP_QUERY = """DELETE FROM user_groups WHERE id = %s"""

    DELETE_ALL_QUERY = """DELETE FROM user_groups"""

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
    def save(self, group_id, category_id) -> str:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_GROUP_QUERY,
                       (group_id, category_id))
        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row

        conn.commit()
        conn.close()

        return str(generated_id)

    # Function to retrieve blob data from SQLite
    def get_by_id(self, id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_QUERY, (id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def list(self) -> list[tuple[Any, ...]]:
        """List all documents"""
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_GROUP_QUERY)
        result = cursor.fetchall()
        conn.close()
        return result

    def list_by_group(self, group_ids) -> List[tuple[Any, ...]]:
        """List all documents"""
        conn = self.build_connection()
        cursor = conn.cursor()
        # Construct placeholders for each group_id
        placeholders = ','.join(['%s'] * len(group_ids))
        # Construct the SQL query with the correct placeholders
        query = self.LIST_CATEGORY_FOR_GROUP_QUERY.format(placeholders)

        # Execute the query with the list of group_ids as parameters
        cursor.execute(query, tuple(group_ids))

        result = cursor.fetchall()
        conn.close()
        return result

    def delete_by_id(self, blob_ids: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_GROUP_QUERY, (blob_ids,))
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
