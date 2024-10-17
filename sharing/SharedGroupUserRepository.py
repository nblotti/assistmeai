from typing import List, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from sharing.SharedGroupUser import SharedGroupUser, SharedGroupUserCreate


class SharedGroupUserRepository(BaseAlchemyRepository):
    SELECT_GROUP_BY_USER_ID_QUERY = """select su.group_id, sg.name, su.creation_date, sg.owner 
    from shared_group_users su, shared_groups sg where su.group_id = sg.id and su.user_id =%s """

    def create(self, group: SharedGroupUserCreate) -> SharedGroupUserCreate:

        try:
            new_group = SharedGroupUser(
                group_id=int(group.group_id),
                user_id=group.user_id
            )
            self.db.add(new_group)
            self.db.commit()
            self.db.refresh(new_group)
            self.db.close()
            group.id = str(new_group.id)
            group.creation_date = new_group.creation_date.strftime("%d.%m.%Y")
            return group
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    def read(self, group_id: int) -> SharedGroupUserCreate:

        stmt = select(SharedGroupUser).where(SharedGroupUser.id == group_id)
        group: SharedGroupUser = self.db.execute(stmt).scalars().first()

        return self.map_to_share_group_user(group)

    def delete(self, group_id: int):

        stmt = delete(SharedGroupUser).where(SharedGroupUser.id == group_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount


    def list_by_group_id(self, group_id: int) -> List[SharedGroupUserCreate]:

        stmt = select(SharedGroupUser).where(SharedGroupUser.group_id == group_id)
        new_groups: Sequence[SharedGroupUser] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[SharedGroupUserCreate] = [
            self.map_to_share_group_user(row)
            for row in new_groups
        ]
        return groups

    def list_by_user_id(self, user_id: str) -> List[SharedGroupUserCreate]:

        stmt = select(SharedGroupUser).where(SharedGroupUser.user_id == user_id)
        new_groups: Sequence[SharedGroupUser] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[SharedGroupUserCreate] = [
            self.map_to_share_group_user(row)
            for row in new_groups
        ]
        return groups

    def map_to_share_group_user(self, group: SharedGroupUser) -> SharedGroupUserCreate:
        return SharedGroupUserCreate(
            id=str(group.id),
            group_id=str(group.group_id),
            user_id=group.user_id,
            creation_date=group.creation_date.strftime("%d.%m.%Y")
        )
