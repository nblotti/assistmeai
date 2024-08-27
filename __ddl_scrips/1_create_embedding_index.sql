-- create the index after having uploaded some test documents
CREATE INDEX ON langchain_pg_embedding USING ivfflat (embedding) WITH (lists = 100);



