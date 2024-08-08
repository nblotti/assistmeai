import os
from datetime import datetime

from langchain_core.messages import BaseMessage
from psycopg2 import connect

from message.Message import Message


class MessageRepository:
    INSERT_MESSAGE_QUERY = "INSERT INTO message (conversation_id,role, content,created_on) VALUES (%s, %s, %s,%s )"
    GET_MESSAGES_BY_CONVERSATION_ID_QUERY = "SELECT id, conversation_id,role,content,created_on from message where conversation_id=%s order by id asc"
    DELETE_MESSAGES_BY_CONVERSATION_ID_QUERY = "DELETE FROM message where conversation_id=%s"
    DELETE_ALL_QUERY = "DELETE FROM message"

    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")

        # Function to store a message data in SQLite
    def save(self, conversation_id, message: BaseMessage):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_MESSAGE_QUERY,
                       (conversation_id, message.type, message.content, datetime.now()))
        conn.commit()
        conn.close()

    def get_all_messages_by_conversation_id(self, conversation_id) -> list[BaseMessage]:
        return self.list_messages(self.GET_MESSAGES_BY_CONVERSATION_ID_QUERY, conversation_id)

    def list_messages(self, messages, arguments):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(messages, (arguments,))
        result = cursor.fetchall()
        conn.close()

        returned: list[BaseMessage] = []
        for row in result:
            returned.append(Message(row[0],row[1], row[2], row[3], row[4]).as_lc_message())
        return returned if returned else []

    def delete_all(self):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL_QUERY)
        conn.commit()
        conn.close()

    def delete_by_conversation_id(self, conversation_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_MESSAGES_BY_CONVERSATION_ID_QUERY, (conversation_id,))
        conn.commit()
        conn.close()

    def build_connection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn

