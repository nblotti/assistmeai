from sqlalchemy import text

from BaseAlchemyRepository import BaseAlchemyRepository


class DocumentsEmbeddingsRepository(BaseAlchemyRepository):
    DELETE_EMBEDDING_QUERY = """DELETE FROM langchain_pg_embedding WHERE cmetadata ->>'blob_id' =:blob_id;"""

    GET_EMBEDDING_QUERY = """SELECT cmetadata ->>'text' FROM langchain_pg_embedding 
    WHERE cmetadata ->>'blob_id' = ANY(:ids)"""

    def delete_embeddings_by_id(self, blob_id: str):
        self.db.execute(text(self.DELETE_EMBEDDING_QUERY), {"blob_id": blob_id})
        self.db.commit()

    def get_embeddings_by_ids(self, blob_ids: [str]):
        blob_ids_tuple = tuple(blob_ids)

        results = self.db.execute(
            text(self.GET_EMBEDDING_QUERY),
            {"ids": blob_ids}
        ).fetchall()

        return results
