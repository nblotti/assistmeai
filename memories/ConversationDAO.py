import sqlite3

from memories.Conversation import Conversation


class ConversationDAO:
    INSERT_CONVERSATION = "INSERT INTO conversation (id, pdf_id, user_id,created_on) VALUES (?, ?, ?,? )"
    GET_CONVERSATION_BY_ID = "SELECT * from message where conversation_id id=?"
    DELETE_CONVERSATION_BY_ID = "DELETE FROM message where conversation_id id=?"

    def __init__(self):
        conn = sqlite3.connect('pdf.sqlite3')

    # Function to store a message data in SQLite
    def save(self, conversation: Conversation):
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.INSERT_CONVERSATION,
                       (conversation.id, conversation.pdf_id, conversation.user_id, conversation.created_on))
        conn.commit()
        conn.close()

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_id(self, conversation_id):
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_ID, (conversation_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None

    def delete(self, conversation_id: str):
        conn = sqlite3.connect('pdf.sqlite3')
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CONVERSATION_BY_ID, (conversation_id,))
        conn.close()
