import os

from psycopg2 import connect

from sharing.Group import Group


class GroupRepository:
    INSERT_GROUP_QUERY = """ INSERT INTO shared_groups ( name, owner, creation_date)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_GROUP_QUERY = """SELECT id,name, owner, creation_date FROM shared_groups WHERE id=%s """

    UPDATE_GROUP_QUERY = """UPDATE shared_groups set name = %s,owner= %s, creation_date= %s where id= %s"""

    DELETE_GROUP_QUERY = """DELETE FROM shared_groups WHERE id = %s"""

    SELECT_GROUP_BY_OWNER_QUERY = """SELECT id,name, owner, creation_date FROM shared_groups WHERE owner=%s """

    DELETE_ALL_QUERY = """DELETE FROM shared_groups"""

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

    def create_group(self, group):

        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_GROUP_QUERY,
                       (group.name, group.owner, group.creation_date))

        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row
        group.id = generated_id
        conn.commit()
        conn.close()
        return group

    def get_group(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_QUERY, (group_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return Group(id=result[0], name=result[1], owner=result[2], creation_date=result[3])
        return None

    def update_group(self, group):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.UPDATE_GROUP_QUERY,
                       (group.name, group.owner, group.creation_date, group.id))

        conn.commit()
        conn.close()
        return group

    def delete_group(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_GROUP_QUERY, (group_id,))
        conn.commit()
        conn.close()

    def list_groups_by_owner(self, owner_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_BY_OWNER_QUERY, (owner_id,))
        result = cursor.fetchall()
        conn.close()

        # Transform each database row into an instance of the Group model
        groups = [
            Group(id=row[0], name=row[1], owner=row[2], creation_date=row[3])
            for row in result
        ]
        return groups

