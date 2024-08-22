import os

from psycopg2 import connect

from sharing.SharedGroupUser import SharedGroupUser


class SharedGroupUserRepository:
    INSERT_GROUP_QUERY = """ INSERT INTO shared_group_users ( group_id, user_id, creation_date)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_GROUP_QUERY = """SELECT id::text,group_id::text, user_id, creation_date FROM shared_group_users WHERE id=%s """

    DELETE_GROUP_QUERY = """DELETE FROM shared_group_users WHERE id = %s"""

    SELECT_GROUP_BY_GROUP_ID_QUERY = """SELECT id::text,group_id::text, user_id, creation_date FROM shared_group_users WHERE group_id=%s """

    DELETE_ALL_QUERY = """DELETE FROM shared_group_users"""

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

    def build_connection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn

    def create(self, group):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_GROUP_QUERY,
                       (group.group_id, group.user_id, group.creation_date))

        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row
        group.id = generated_id
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
            return SharedGroupUser(id=result[0], group_id=result[1], user_id=result[2], creation_date=result[3])
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
            SharedGroupUser(id=row[0], group_id=row[1], user_id=row[2], creation_date=row[3])
            for row in result
        ]
        return groups
