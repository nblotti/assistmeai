CREATE TABLE shared_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    owner VARCHAR NOT NULL,
    creation_date DATE NOT NULL
);

CREATE INDEX ix_groups_id ON shared_groups (id);

CREATE TABLE document_share (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    creation_date DATE NOT NULL
);

-- Creating an index on group_id to improve query performance when filtering by group_id
CREATE INDEX idx_group_id ON document_share (group_id);

-- Creating an index on document_id to improve query performance when filtering by document_id
CREATE INDEX idx_document_id ON Share (document_id);