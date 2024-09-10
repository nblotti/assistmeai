from typing import Any, List, Tuple

from BaseRepository import BaseRepository


class CategoryRepository(BaseRepository):
    INSERT_CATEGORY_QUERY = """INSERT INTO document_category (category_name)  VALUES ( %s) RETURNING id;"""

    DELETE_CATEGORY_QUERY = """DELETE FROM document_category WHERE  id = %s"""

    DELETE_ALL_CATEGORY = """DELETE FROM document_category"""

    LIST_ALL_CATEGORY_BY_IDS = """SELECT group_id, category_id, category_name FROM category_by_group WHERE group_id = ANY(%s::text[])"""

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
