import json
import sqlite3
from datetime import datetime

from langchain_core.messages import BaseMessage

from memories.Message import Message


class MessageDAO:
    INSERT_PDF = "INSERT INTO message (conversation_id,document_id, role, content,created_on) VALUES (?, ?, ?,?,? )"
    GET_DOCUMENTS_BY_CONVERSATION_ID = "SELECT * from message where conversation_id=? and document_id=?"
    DELETE_DOCUMENTS_BY_CONVERSATION_ID = "DELETE FROM message where conversation_id=? and document_id=?"

    # Function to store a message data in SQLite
    def save(self, conversation_id, document_id, message: BaseMessage):
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.INSERT_PDF,
                       (conversation_id, document_id, message.type, message.content, datetime.now()))
        conn.commit()
        conn.close()

    # Function to get all messages  by conversation_id data from SQLite
    def get_all_messages_by_conversation_id_and_document_id(self, conversation_id, document_id) -> list[BaseMessage]:
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.GET_DOCUMENTS_BY_CONVERSATION_ID, (conversation_id,document_id))
        result = cursor.fetchall()
        conn.close()

        returned: list[BaseMessage] = []
        for row in result:
            returned.append(Message(row[0], row[1], row[2], row[3], row[4], row[5]).as_lc_message())

        return returned if returned else []

    def delete_documents_by_conversation_id_and_document_id(self, conversation_id: str, document_id:str):
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.DELETE_DOCUMENTS_BY_CONVERSATION_ID, (conversation_id,document_id))
        conn.close()
