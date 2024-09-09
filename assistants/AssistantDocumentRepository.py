import os

from psycopg2 import connect

from assistants.AssistantsDocument import AssistantsDocument


class AssistantDocumentRepository:
    INSERT_ASSISTANT_DOCUMENT__QUERY = """ INSERT INTO assistants_document (assistant_id, document_id, document_name)  VALUES ( %s, %s, %s) RETURNING id;"""

    LIST_ASSISTANT_DOCUMENT_QUERY = """SELECT id::text,assistant_id::text, document_id::text, document_name FROM assistants_document WHERE assistant_id=%s """

    DELETE_GROUP_QUERY = """DELETE FROM assistants_document WHERE id = %s"""

    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, ):
        self.db_name = os.getenv("DB_NAME")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")

    def build_connection(self):
        conn = connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port
        )
        return conn

    def create(self, assistant_document):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.INSERT_ASSISTANT_DOCUMENT__QUERY,
                       (assistant_document.assistant_id, assistant_document.document_id,
                        assistant_document.document_name))

        generated_id = cursor.fetchone()[0]  # Fetch the first column of the first row
        assistant_document.id = generated_id
        conn.commit()
        conn.close()
        return assistant_document

    def delete(self, assistant_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_GROUP_QUERY, (assistant_id,))
        conn.commit()
        conn.close()

    def list_by_assistant_id(self, assistant_id):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.LIST_ASSISTANT_DOCUMENT_QUERY, (assistant_id,))
        result = cursor.fetchall()
        conn.close()

        # Transform each database row into an instance of the Group model
        assistants_documents = [
            AssistantsDocument(id=row[0], assistant_id=row[1], document_id=row[2], document_name=row[3])
            for row in result
        ]
        return assistants_documents
