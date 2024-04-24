import json
from datetime import datetime

from psycopg2 import connect

import config
from chat.Conversation import Conversation


class ConversationDAO:
    INSERT_DOCUMENT_CONVERSATION = "INSERT INTO conversation (document_id, user_id) VALUES (%s, %s) RETURNING id, created_on;"
    INSERT_STANDALONE_CONVERSATION = "INSERT INTO conversation ( user_id) VALUES (%s) RETURNING id, created_on;"

    GET_CONVERSATION_BY_USER_ID = """SELECT c.id,c.user_id, c.description, c.document_id, 
    COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
    left outer join  pdf p on c.document_id = p.id where c.user_id=%s"""

    GET_CONVERSATION_BY_ID = """SELECT c.id,c.user_id, c.description, c.document_id, 
    COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
    left outer join  pdf p on c.document_id = p.id where c.id=%s"""

    GET_CONVERSATION_COUNT_BY_DOCUMENT_ID = """SELECT count(*) from conversation c where c.document_id=%s"""

    DELETE_CONVERSATION_BY_ID = "DELETE FROM conversation where id=%s"
    DELETE_CONVERSATION_BY_DOCUMENT_ID = "DELETE FROM conversation where document_id=%s"
    DELETE_ALL = "DELETE FROM conversation"

    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, db_name: str, db_host: str, db_port: str, db_user: str, db_password: str):
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

    # Function to store a message data in SQLite
    def save(self, conversation: Conversation):
        conn = self.buildConnection()
        cursor = conn.cursor()
        if conversation.pdf_id is not None and len(conversation.pdf_id) != 0:
            cursor.execute(self.INSERT_DOCUMENT_CONVERSATION,
                           (conversation.pdf_id, conversation.user_id))
        else:
            cursor.execute(self.INSERT_STANDALONE_CONVERSATION,
                           conversation.user_id)

        row = cursor.fetchone()
        conversation.id = row[0]
        conversation.created_on = row[1].strftime("%d.%m.%Y")
        conn.commit()
        conn.close()
        return conversation

    def get_conversation_by_id(self, document_id) -> Conversation:
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_ID, (document_id,))
        row = cursor.fetchone()

        conversation = Conversation(id=row[0], user_id=row[1], description=row[2], pdf_id=row[3], pdf_name=row[4],
                                    created_on=row[5].strftime("%d.%m.%Y"))

        conn.close()
        return conversation

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_user_id(self, user_id):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_USER_ID, (user_id,))
        rows = cursor.fetchall()

        conversations = [
            Conversation(id=row[0], user_id=row[1], description=row[2], pdf_id=row[3], pdf_name=row[4],
                         created_on=row[5].strftime("%d.%m.%Y")).dict()
            for row in rows]

        conn.close()
        return conversations

    def delete(self, id: str):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CONVERSATION_BY_ID, (id,))
        conn.commit()
        conn.close()

    def delete_by_file_id(self, blob_id: str):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CONVERSATION_BY_DOCUMENT_ID, (blob_id,))
        conn.commit()
        conn.close()

    def delete_all(self):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL)
        conn.commit()
        conn.close()


    def get_conversation_count_by_document_id(self, pdf_id):
        conn = self.buildConnection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_COUNT_BY_DOCUMENT_ID, (pdf_id,))

        count = cursor.fetchone()[0]

        conn.close()
        return count

    def buildConnection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn