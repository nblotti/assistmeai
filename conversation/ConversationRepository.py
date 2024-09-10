from BaseRepository import BaseRepository
from conversation.Conversation import Conversation


class ConversationRepository(BaseRepository):
    INSERT_DOCUMENT_CONVERSATION_QUERY = """INSERT INTO conversation (document_id, perimeter) VALUES (%s, 
    %s) RETURNING id, created_on;"""
    INSERT_STANDALONE_CONVERSATION_QUERY = """INSERT INTO conversation (perimeter) VALUES (%s) RETURNING id, 
    created_on;"""

    GET_CONVERSATION_BY_PERIMETER_QUERY = """SELECT c.id, c.perimeter,c.description, c.document_id,COALESCE(p.name, '') 
    AS document_name,c.created_on FROM conversation c 
    LEFT JOIN document p ON c.document_id = p.id 
    LEFT JOIN assistants a ON a.conversation_id::TEXT = c.id::TEXT 
    WHERE c.perimeter = %s AND a.conversation_id IS NULL;"""

    GET_CONVERSATION_BY_ID_QUERY = """SELECT c.id,c.perimeter, c.description, c.document_id, 
    COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
    left outer join  document p on c.document_id = p.id where c.id=%s"""

    GET_CONVERSATION_BY_FILE_ID_QUERY = """SELECT c.id,c.perimeter, c.description, c.document_id, 
      COALESCE(p.name, '') AS document_name, c.created_on FROM conversation c 
      left outer join  document p on c.document_id = p.id where c.document_id=%s and c.perimeter=%s
      order by c.created_on DESC"""

    GET_CONVERSATION_COUNT_BY_DOCUMENT_ID_QUERY = """SELECT count(*) from conversation c where c.document_id=%s"""

    DELETE_CONVERSATION_BY_ID_QUERY = "DELETE FROM conversation where id=%s"
    DELETE_CONVERSATION_BY_DOCUMENT_ID_QUERY = "DELETE FROM conversation where document_id=%s"
    DELETE_ALL_QUERY = "DELETE FROM conversation"

    # Function to store a message data in SQLite

    def save(self, conversation: Conversation):
        conn = self.build_connection()
        cursor = conn.cursor()
        if conversation.pdf_id is not None and conversation.pdf_id != 0:
            cursor.execute(self.INSERT_DOCUMENT_CONVERSATION_QUERY,
                           (conversation.pdf_id, conversation.perimeter))
        else:
            cursor.execute(self.INSERT_STANDALONE_CONVERSATION_QUERY, (conversation.perimeter,))

        row = cursor.fetchone()
        conversation.id = row[0]
        conversation.created_on = row[1].strftime("%d.%m.%Y")
        conn.commit()
        conn.close()
        return conversation

    def get_conversation_by_id(self, conversation_id) -> Conversation:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_ID_QUERY, (conversation_id,))
        row = cursor.fetchone()

        conversation = Conversation(id=row[0], perimeter=row[1], description=row[2], pdf_id=row[3], pdf_name=row[4],
                                    created_on=row[5].strftime("%d.%m.%Y"))

        conn.close()
        return conversation

    # Function to get all messages  by conversation_id data from SQLite
    def get_conversation_by_perimeter(self, perimeter):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_PERIMETER_QUERY, (perimeter,))
        rows = cursor.fetchall()

        conversations = [
            Conversation(id=row[0], perimeter=row[1], description=row[2], pdf_id=row[3], pdf_name=row[4],
                         created_on=row[5].strftime("%d.%m.%Y")).dict()
            for row in rows]

        conn.close()
        return conversations

    def delete(self, id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CONVERSATION_BY_ID_QUERY, (id,))
        conn.commit()
        conn.close()

    def delete_by_file_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_CONVERSATION_BY_DOCUMENT_ID_QUERY, (blob_id,))
        conn.commit()
        conn.close()

    def delete_all(self):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ALL_QUERY)
        conn.commit()
        conn.close()

    def get_conversation_by_document_id(self, document_id, user_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_BY_FILE_ID_QUERY, (document_id, user_id))
        rows = cursor.fetchall()

        conversations = [
            Conversation(id=row[0], perimeter=row[1], description=row[2], pdf_id=row[3], pdf_name=row[4],
                         created_on=row[5].strftime("%d.%m.%Y")).dict()
            for row in rows]

        conn.close()
        return conversations

    def get_conversation_count_by_document_id(self, pdf_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_CONVERSATION_COUNT_BY_DOCUMENT_ID_QUERY, (pdf_id,))

        count = cursor.fetchone()[0]

        conn.close()
        return count
