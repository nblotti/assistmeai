import os

from fastapi import File

from chat import DocumentsDAO
from chat.Conversation import Conversation
from chat.ConversationDAO import ConversationDAO
from chat.MessageDAO import MessageDAO
from embeddings import EmbeddingRepository


class InteractionManager:
    def __init__(self, embedding_repository: EmbeddingRepository, postgres_dao: DocumentsDAO,
                 conversation_dao: ConversationDAO, message_dao: MessageDAO):
        self.embedding_repository = embedding_repository
        self.postgres_dao = postgres_dao
        self.conversation_dao = conversation_dao
        self.message_dao = message_dao

    '''
        This method store a new file in Postgres database, then create embeddings and conversation
        It returns the id of the file and the filename, as well as the conversation id        
    '''

    async def upload_file(self, file: File, perimeter: str):

        contents = await file.read()

        blob_id = self.postgres_dao.save(file.filename, perimeter, contents)

        temp_file = "./" + blob_id + ".files"
        with open(temp_file, "wb") as file_w:
            file_w.write(contents)

        self.embedding_repository.create_embeddings_for_pdf(blob_id, perimeter, temp_file)
        conversation = Conversation(
            perimeter=perimeter,
            pdf_id=blob_id,
        )
        conversation = self.conversation_dao.save(conversation)

        self.delete_temporary_disk_file(temp_file)

        return {"filename": file.filename, "blob_id": blob_id, "conversation_id": conversation.id}

    '''
        This method deletes a temporary file on the HD
    '''

    def delete_temporary_disk_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")

    def download_blob(self, blob_id: str):
        return self.postgres_dao.get_by_id(blob_id)

    def list_document(self):
        return self.postgres_dao.list()

    '''
        This method deletes a file in Postgres database and all associated embeddings and conversations
    '''

    def delete(self, blob_id: str):
        self.embedding_repository.delete_embeddings_by_file_id(blob_id)
        self.conversation_dao.delete_by_file_id(blob_id)
        return self.postgres_dao.delete_by_ids(blob_id)

    def delete_all(self):
        self.embedding_repository.delete_all_embeddings()
        self.conversation_dao.delete_all()
        self.postgres_dao.delete_all()
        self.message_dao.delete_all()

    def get_document(self, pdf_id):
        return self.postgres_dao.get_by_id(pdf_id)

    '''
        This method deletes a conversation in Postgres database. If a file is associated to the conversation,
         then the file and associated embeddings are deleted as well
    '''

    def delete_by_conversation_id(self, conversation_id):
        conversation = self.conversation_dao.get_conversation_by_id(conversation_id)
        count = self.conversation_dao.get_conversation_count_by_document_id(conversation.pdf_id)

        if conversation.pdf_id != -1 and count == 1:
            self.delete(conversation.pdf_id)
        else:
            self.conversation_dao.delete(conversation_id)

    def get_conversation_by_perimeter(self, perimeter):
        return self.conversation_dao.get_conversation_by_perimeter(perimeter)

    def get_conversation_by_id(self, perimeter):
        return self.conversation_dao.get_conversation_by_id(perimeter)

    def save(self, conversation):
        res = self.conversation_dao.save(conversation)
        if res.pdf_id != "":
            doc = self.postgres_dao.get_by_id(res.pdf_id)
            res.pdf_name = doc[0]
        return res

    def get_messages(self, conversation_id):
        return self.message_dao.get_all_messages_by_conversation_id(conversation_id)

    def save_message(self, conversation_id, message):
        return self.message_dao.save(conversation_id, message)

    def delete_message_by_conversation_id(self, conversation_id):
        pass
