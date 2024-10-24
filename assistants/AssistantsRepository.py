from typing import Sequence

from sqlalchemy import select

from BaseAlchemyRepository import BaseAlchemyRepository
from assistants.Assistant import Assistant, AssistantCreate


class AssistantsRepository(BaseAlchemyRepository):

    def save(self, assistant: AssistantCreate):
        new_assistant = Assistant(
            user_id=assistant.userid,
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
        assistant.id = new_assistant.id
        return assistant

    def update(self, assistant: AssistantCreate):
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
        stmt = select(Assistant).where(Assistant.conversation_id == int(conversation_id))
        assistant: Assistant = self.db.execute(stmt).scalars().first()

        return self.map_to_assistant(assistant)

    def get_all_assistant_by_user_id(self, user_id) -> list[AssistantCreate]:
        stmt = select(Assistant).where(Assistant.user_id == user_id)
        assistants: Sequence[Assistant] = self.db.execute(stmt).scalars().all()

        return [self.map_to_assistant(assistant) for assistant in assistants]

    def delete_by_assistant_id(self, assistant_id):
        affected_rows = self.db.query(Assistant).filter(Assistant.id == int(assistant_id)).delete(
            synchronize_session='auto')
        self.db.commit()
        return affected_rows

    def map_to_assistant(self, db_assistant: Assistant) -> AssistantCreate:
        assistant = AssistantCreate(
            id=str(db_assistant.id),
            userid=str(db_assistant.user_id),
            name=db_assistant.name,
            conversation_id=str(db_assistant.conversation_id),
            description=db_assistant.description,
            gpt_model_number=db_assistant.gpt_model_number,
            use_documents=db_assistant.use_documents,
            favorite=db_assistant.favorite
        )

        return assistant
