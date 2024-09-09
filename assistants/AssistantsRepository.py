import os

from psycopg2 import connect

from assistants.Assistant import Assistant


class AssistantsRepository:
    INSERT_ASSISTANT_QUERY = (
        "INSERT INTO assistants (user_id,name, conversation_id,description,gpt_model_number,use_documents) "
        "VALUES (%s, %s, %s,%s ,%s, %s) RETURNING id")
    UPDATE_ASSISTANT_QUERY = "UPDATE assistants set name = %s,description= %s, gpt_model_number= %s, use_documents= %s where id= %s"
    GET_ASSISTANT_BY_USER_QUERY = ("SELECT id::text AS id,user_id,conversation_id::text AS conversation_id,"
                                   "name,  description ,gpt_model_number, use_documents from assistants where user_id=%s order by id ")
    GET_ASSISTANT_BY_CONVERSATION_ID_QUERY = ("SELECT id::text AS id,user_id,conversation_id::text AS conversation_id,"
                                              "name,  description, gpt_model_number, use_documents from assistants where "
                                              "conversation_id=%s ")
    DELETE_ASSISTANT_BY_ASSISTANT_ID_QUERY = "DELETE FROM assistants where id=%s"
    DELETE_ALL_QUERY = "DELETE FROM assistants"

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

    def save(self, assistant):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_ASSISTANT_QUERY,
                       (assistant.userid, assistant.name, assistant.conversation_id, assistant.description,
                        assistant.gpt_model_number, assistant.use_documents))

        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row
        assistant.id = generated_id
        conn.commit()
        conn.close()
        return assistant

    def update(self, assistant):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.UPDATE_ASSISTANT_QUERY,
                       (assistant.name, assistant.description, assistant.gpt_model_number, assistant.use_documents,
                        assistant.id))

        conn.commit()
        conn.close()
        return assistant

    def get_assistant_by_conversation_id(self, conversation_id) -> Assistant:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_ASSISTANT_BY_CONVERSATION_ID_QUERY, (conversation_id,))
        result = cursor.fetchone()
        conn.close()

        return Assistant(
            id=result[0],
            userid=result[1],
            conversation_id=result[2],
            name=result[3],
            description=result[4],
            gpt_model_number=result[5],
            use_documents=result[6]
            )

    def get_all_assistant_by_user_id(self, user_id) -> list[Assistant]:
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.GET_ASSISTANT_BY_USER_QUERY, (user_id,))
        result = cursor.fetchall()
        conn.close()

        returned: list[Assistant] = []
        for row in result:
            returned.append(Assistant(
                id=row[0],
                userid=row[1],
                conversation_id=row[2],
                name=row[3],
                description=row[4],
                gpt_model_number=row[5],
                use_documents=row[6]))
        return returned if returned else []

    def delete_by_assistant_id(self, assistant_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ASSISTANT_BY_ASSISTANT_ID_QUERY, (assistant_id,))
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
