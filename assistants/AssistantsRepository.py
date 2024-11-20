from typing import Sequence

from sqlalchemy import select

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.Assistant import Assistant, AssistantCreate


class AssistantsRepository(BaseAlchemyRepository):
    """
    Repository for managing assistants.

    This class provides methods to perform CRUD operations on assistants using SQLAlchemy. It includes
    methods to save, update, delete, and retrieve assistant records from the database.

    :ivar db: The database session used for performing operations.
    :type db: Session
    """
    def save(self, assistant: AssistantCreate):
        new_assistant = Assistant(
            user_id=assistant.user_id,
            name=assistant.name,
            conversation_id=int(assistant.conversation_id),
            description=assistant.description,
            gpt_model_number=assistant.gpt_model_number,
            use_documents=assistant.use_documents,
            favorite=assistant.favorite

        )
        self.db.add(new_assistant)
        self.db.commit()
        self.db.refresh(new_assistant)
        assistant.id = str(new_assistant.id)
        return assistant

    def update(self, assistant: AssistantCreate):
        """
        Updates an existing Assistant record in the database with the details provided in the
        AssistantCreate object.

        This function fetches the Assistant record from the database that matches the given
        id (from the AssistantCreate object 'assistant'). If found, it updates the name,
        description, gpt_model_number, use_documents, and favorite attributes of the Assistant
        record. Commits the changes to the database and refreshes the record before mapping
        and returning the updated Assistant.

        :param assistant: The AssistantCreate object containing updated attributes.
        :type assistant: AssistantCreate
        :return: The updated Assistant object after saving the changes.
        :rtype: Assistant
        """
        stmt = select(Assistant).where(Assistant.id == int(assistant.id))
        assistant_to_update: Assistant = self.db.execute(stmt).scalars().first()

        if assistant_to_update:
            assistant_to_update.name = assistant.name
            assistant_to_update.description = assistant.description
            assistant_to_update.gpt_model_number = assistant.gpt_model_number
            assistant_to_update.use_documents = assistant.use_documents
            assistant_to_update.favorite = assistant.favorite
            self.db.commit()
            self.db.refresh(assistant_to_update)

        return self.map_to_assistant(assistant_to_update)

    def get_assistant_by_conversation_id(self, conversation_id: str) -> AssistantCreate:
        """
        Retrieve an assistant by the given conversation ID.

        This method queries the database to find an assistant associated with the
        specified conversation ID. The resulting assistant is then mapped to an
        AssistantCreate object and returned.

        :param conversation_id: The ID of the conversation to find the assistant for.
        :type conversation_id: str
        :return: An AssistantCreate object representing the found assistant.
        :rtype: AssistantCreate
        """
        stmt = select(Assistant).where(Assistant.conversation_id == int(conversation_id))
        assistant: Assistant = self.db.execute(stmt).scalars().first()

        return self.map_to_assistant(assistant)

    def get_all_assistant_by_user_id(self, user_id) -> list[AssistantCreate]:
        """
        Fetches all assistants associated with the given user id.

        This method retrieves all assistant records that match the provided
        user id from the database. It then maps each record to an instance
        of AssistantCreate and returns a list of these instances.

        :param user_id: The ID of the user for whom to fetch assistants.
        :type user_id: int
        :return: A list of AssistantCreate objects representing the assistants.
        :rtype: list[AssistantCreate]
        """
        stmt = select(Assistant).where(Assistant.user_id == user_id)
        assistants: Sequence[Assistant] = self.db.execute(stmt).scalars().all()

        return [self.map_to_assistant(assistant) for assistant in assistants]

    def delete_by_assistant_id(self, assistant_id):
        """
        Deletes an assistant from the database by the given assistant_id.

        This method queries the Assistant table, filters by the given
        assistant_id, deletes the record, and commits the change to the
        database. It returns the number of rows affected by the deletion.

        :param assistant_id: The ID of the assistant to delete.
        :type assistant_id: int
        :return: The number of rows affected by the deletion.
        :rtype: int
        """
        affected_rows = self.db.query(Assistant).filter(Assistant.id == int(assistant_id)).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def map_to_assistant(self, db_assistant: Assistant) -> AssistantCreate:
        """
        Maps a database Assistant object to an AssistantCreate object.

        This method assumes the `db_assistant` parameter is an instance of the
        `Assistant` class and returns an instance of `AssistantCreate`. Each
        attribute of `db_assistant` is converted to match the corresponding
        attribute in `AssistantCreate`.

        :param db_assistant: The database Assistant object to be mapped
        :type db_assistant: Assistant
        :return: The newly created AssistantCreate object
        :rtype: AssistantCreate
        """
        assistant = AssistantCreate(
            id=str(db_assistant.id),
            user_id=str(db_assistant.user_id),
            name=db_assistant.name,
            conversation_id=str(db_assistant.conversation_id),
            description=db_assistant.description,
            gpt_model_number=db_assistant.gpt_model_number,
            use_documents=db_assistant.use_documents,
            favorite=db_assistant.favorite
        )

        return assistant
