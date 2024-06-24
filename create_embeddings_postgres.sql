
------------------------------------------------------------------------------------------------------------------------
-- index on embeddings, run only after some documents have been inserted

CREATE INDEX ON langchain_pg_embedding USING ivfflat (embedding) WITH (lists = 100);