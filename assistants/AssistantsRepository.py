from BaseRepository import BaseRepository
from assistants.Assistant import Assistant


class AssistantsRepository(BaseRepository):
    """
    AssistantsRepository class for managing assistant-related database operations

    Attributes:
        INSERT_ASSISTANT_QUERY (str): SQL query template for inserting a new assistant.
        UPDATE_ASSISTANT_QUERY (str): SQL query template for updating an existing assistant.
        GET_ASSISTANT_BY_USER_QUERY (str): SQL query template for retrieving assistants by user ID.
        GET_ASSISTANT_BY_CONVERSATION_ID_QUERY (str): SQL query template for retrieving an assistant by conversation ID.
        DELETE_ASSISTANT_BY_ASSISTANT_ID_QUERY (str): SQL query template for deleting an assistant by ID.
        DELETE_ALL_QUERY (str): SQL query template for deleting all assistants.

    Methods:
        save(assistant):
            Inserts a new assistant into the database and returns the generated assistant ID.

        update(assistant):
            Updates an existing assistant's information in the database.

        get_assistant_by_conversation_id(conversation_id):
            Retrieves an assistant from the database by conversation ID.

        get_all_assistant_by_user_id(user_id):
            Retrieves all assistants associated with a specific user from the database.

        delete_by_assistant_id(assistant_id):
            Deletes an assistant from the database by assistant ID.
    """
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

    # Function to store a message data in SQLite

    def save(self, assistant):
        """
        :param assistant: An instance of the Assistant class containing assistant details such as userid, name, conversation_id, description, gpt_model_number, and use_documents.
        :return: The updated Assistant instance with the generated id populated.
        """
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
        """
        :param conversation_id: Unique identifier of the conversation to fetch the assistant for.
        :return: An Assistant object containing details associated with the given conversation_id.
        """
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
        """
        :param user_id: The ID of the user for whom the assistants are being retrieved.
        :return: A list of Assistant objects associated with the given user ID.
        """
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
        """
        :param assistant_id: The unique identifier of the assistant to be deleted.
        :return: None.
        """
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_ASSISTANT_BY_ASSISTANT_ID_QUERY, (assistant_id,))
        conn.commit()
        conn.close()
