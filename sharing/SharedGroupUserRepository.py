from BaseRepository import BaseRepository
from sharing.SharedGroupUser import SharedGroupUser
from sharing.SharedGroupUserDTO import SharedGroupUserDTO


class SharedGroupUserRepository(BaseRepository):
    INSERT_GROUP_QUERY = """ INSERT INTO shared_group_users ( group_id, user_id, creation_date)  VALUES ( %s, %s, %s) RETURNING id;"""

    SELECT_GROUP_QUERY = """SELECT id::text,group_id::text, user_id, creation_date FROM shared_group_users WHERE id=%s """

    DELETE_GROUP_QUERY = """DELETE FROM shared_group_users WHERE id = %s"""

    SELECT_GROUP_BY_GROUP_ID_QUERY = """SELECT id::text,group_id::text, user_id, creation_date FROM shared_group_users WHERE group_id=%s """

    SELECT_GROUP_BY_USER_ID_QUERY = """select su.group_id, sg.name, su.creation_date, sg.owner 
    from shared_group_users su, shared_groups sg where su.group_id = sg.id and su.user_id =%s """

    DELETE_ALL_QUERY = """DELETE FROM shared_group_users"""

    def create(self, group):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_GROUP_QUERY,
                       (group.group_id, group.user_id, group.creation_date))

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
            return SharedGroupUser(id=result[0], group_id=result[1], user_id=result[2], creation_date=result[3])
        return None

    def delete(self, group_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_GROUP_QUERY, (group_id,))
        conn.commit()
        conn.close()

    def list_by_user_id(self, user_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.SELECT_GROUP_BY_USER_ID_QUERY, (user_id,))
        result = cursor.fetchall()
        conn.close()

        # Transform each database row into an instance of the Group model
        groups = [
            SharedGroupUserDTO(group_id=row[0], name=row[1], creation_date=row[2], owner=row[3])
            for row in result
        ]
        return groups

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
