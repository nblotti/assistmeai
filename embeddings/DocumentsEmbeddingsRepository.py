from BaseRepository import BaseRepository


class DocumentsEmbeddingsRepository(BaseRepository):
    DELETE_EMBEDDING_QUERY = """DELETE FROM langchain_pg_embedding WHERE cmetadata ->>'blob_id' =%s;"""

    GET_EMBEDDING_QUERY = """SELECT cmetadata ->>'text' FROM langchain_pg_embedding 
    WHERE cmetadata ->>'blob_id' in %s;"""

    def delete_embeddings_by_id(self, blob_id: str):
        conn = self.build_connection()
        cursor = conn.cursor()
        cursor.execute(self.DELETE_EMBEDDING_QUERY, (blob_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def get_embeddings_by_ids(self, blob_ids: [str]):
        conn = self.build_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(self.GET_EMBEDDING_QUERY,
                           (tuple(blob_ids),))  # Secure way to pass the list parameter to the query
            results = cursor.fetchall()
        finally:
            conn.commit()  # Commit the transaction if any
            cursor.close()
            conn.close()

        return results
