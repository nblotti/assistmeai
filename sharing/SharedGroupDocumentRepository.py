from BaseRepository import BaseRepository
from sharing.SharedGroupDocument import SharedGroupDocument


class SharedGroupDocumentRepository(BaseRepository):
    INSERT_GROUP_QUERY = """INSERT INTO shared_group_document ( group_id, document_id, creation_date)  
    VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_GROUP_QUERY = """SELECT id::text,group_id::text, document_id::text, creation_date 
    FROM shared_group_document WHERE id=%s """

    DELETE_GROUP_QUERY = """DELETE FROM shared_group_document WHERE id = %s"""

    SELECT_GROUP_BY_GROUP_ID_QUERY = """SELECT id::text,group_id::text, document_id::text, creation_date 
    FROM shared_group_document WHERE group_id=%s """

    DELETE_ALL_QUERY = """DELETE FROM shared_group_document"""

    def create(self, group):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_GROUP_QUERY,
                       (group.group_id, group.document_id, group.creation_date))

        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row
        group.id = str(generated_id)
        conn.commit()
        conn.close()
        return group

    def read(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_QUERY, (group_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return SharedGroupDocument(id=result[0], document_id=result[1], group_id=result[2], creation_date=result[3])
        return None

    def delete(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_GROUP_QUERY, (group_id,))
        conn.commit()
        conn.close()

    def list_by_group_id(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_BY_GROUP_ID_QUERY, (group_id,))
        result = cursor.fetchall()
        conn.close()

        # Transform each database row into an instance of the Group model
        groups = [
            SharedGroupDocument(id=row[0], document_id=row[2], group_id=row[1], creation_date=row[3])
            for row in result
        ]
        return groups
