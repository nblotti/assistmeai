from typing import List, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from rights.User import UserGroup, UserGroupCreate


class UserRepository(BaseAlchemyRepository):

    def save(self, group: UserGroupCreate) -> UserGroupCreate:

        try:
            new_group = UserGroup(

                group_id=group.group_id,
                category_id=int(group.category_id)
            )
            self.db.add(new_group)
            self.db.commit()
            self.db.refresh(new_group)
            self.db.close()
            group.id = str(new_group.id)
            return group
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {e}")
            raise
        finally:
            self.db.close()

    # Function to retrieve blob data from SQLite
    def get_by_id(self, group_id: int) -> UserGroupCreate:
        stmt = select(UserGroup).where(UserGroup.id == group_id)
        group: UserGroup = self.db.execute(stmt).scalars().first()

        return self.map_to_user_group(group)

    def list(self) -> list[UserGroupCreate]:

        stmt = select(UserGroup)
        new_groups: Sequence[UserGroup] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[UserGroupCreate] = [
            self.map_to_user_group(row)
            for row in new_groups
        ]
        return groups

    def list_by_group(self, group_ids) -> List[UserGroupCreate]:
        """List all documents"""

        stmt = select(UserGroup).where(UserGroup.group_id.in_(group_ids))
        new_groups: Sequence[UserGroup] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[UserGroupCreate] = [
            self.map_to_user_group(row)
            for row in new_groups
        ]
        return groups

    def delete_by_id(self, group_id: int):
        stmt = delete(UserGroup).where(UserGroup.id == group_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def map_to_user_group(self, group: UserGroup) -> UserGroupCreate:
        return UserGroupCreate(
            id=str(group.id),
            group_id=group.group_id,
            category_idr=str(group.category_id),
            is_admin=group.is_admin
        )
