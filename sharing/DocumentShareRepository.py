import os

from psycopg2 import connect


class DocumentShareRepository:

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

    def create_share(self, group):
        pass

    def get_share(self, group_id):
        pass

    def update_share(self, group):
        pass

    def delete_share(self, group_id):
        pass

    def list_shares_by_owner(self, owner_id):
        pass

