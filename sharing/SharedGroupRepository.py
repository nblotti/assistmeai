from typing import List, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from BaseAlchemyRepository import BaseAlchemyRepository
from sharing.SharedGroup import SharedGroupCreate, SharedGroup
from sharing.SharedGroupUser import SharedGroupUser


class SharedGroupRepository(BaseAlchemyRepository):
    UPDATE_GROUP_QUERY = """UPDATE shared_groups set name = %s,owner= %s, creation_date= %s where id= %s"""

    def create(self, group: SharedGroupCreate) -> SharedGroupCreate:

        try:
            new_group = SharedGroup(
                name=group.name,
                owner=group.owner
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

    def read(self, group_id: int) -> SharedGroupCreate:
        stmt = select(SharedGroup).where(SharedGroup.id == group_id)
        group: SharedGroup = self.db.execute(stmt).scalars().first()

        return self.map_to_share_group(group)

    def update(self, updated_group: SharedGroupCreate):

        stmt = select(SharedGroup).where(SharedGroup.id == int(updated_group.id))

        group: SharedGroup = self.db.execute(stmt).scalars().first()
        group.name = updated_group.name
        group.owner = updated_group.owner

        self.db.commit()

        return updated_group

    def delete(self, group_id: int):
        stmt = delete(SharedGroup).where(SharedGroup.id == group_id)
        affected_rows = self.db.execute(stmt)
        self.db.commit()
        return affected_rows.rowcount

    def list_by_owner(self, owner: str) -> List[SharedGroupCreate]:
        stmt = select(SharedGroup).where(SharedGroup.owner == owner)
        new_groups: Sequence[SharedGroup] = self.db.execute(stmt).scalars().all()

        # Transform each database row into an instance of the Group model
        groups: List[SharedGroupCreate] = [
            self.map_to_share_group(row)
            for row in new_groups
        ]
        return groups

    def list_groups_by_user_id(self, user_id) -> List[SharedGroupCreate]:

        results = self.db.query(SharedGroup, SharedGroupUser).join(SharedGroup,
                                                                   SharedGroupUser.group_id == SharedGroup.id,
                                                                   isouter=True).filter(
            SharedGroupUser.user_id == user_id).all()

        shared_groups = []
        for shared_group, shared_group_user in results:
            new_shared_group = self.map_to_share_group(shared_group)
            shared_groups.append(new_shared_group)

        return shared_groups

    def map_to_share_group(self, group: SharedGroup) -> SharedGroupCreate:
        return SharedGroupCreate(
            id=str(group.id),
            name=str(group.name),
            owner=str(group.owner),
            creation_date=group.creation_date.strftime("%d.%m.%Y")
        )
