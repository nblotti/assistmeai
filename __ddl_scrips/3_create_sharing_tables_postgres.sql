CREATE TABLE shared_groups
(
    id            INT DEFAULT nextval('owner_sequence') PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    owner         VARCHAR(255) NOT NULL,
    creation_date DATE    NOT NULL
);

CREATE INDEX ix_groups_id ON shared_groups (id);

CREATE TABLE shared_group_users
(
    id            SERIAL PRIMARY KEY,
    group_id      integer NOT NULL,
    user_id       VARCHAR(255) NOT NULL,
    creation_date DATE    NOT NULL,
    FOREIGN KEY (group_id) REFERENCES shared_groups (id) ON DELETE CASCADE,
    CONSTRAINT unique_group_user UNIQUE (group_id, user_id)
);

-- Creating an index on group_id to improve query performance when filtering by group_id
CREATE INDEX idx_user_id ON shared_group_users (group_id);

CREATE TABLE shared_group_document
(
    id            SERIAL PRIMARY KEY,
    group_id      integer NOT NULL,
    document_id   integer NOT NULL,
    creation_date DATE    NOT NULL,
    FOREIGN KEY (group_id) REFERENCES shared_groups (id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES document (id) ON DELETE CASCADE
);

-- Creating an index on group_id to improve query performance when filtering by group_id
CREATE INDEX idx_group_id ON shared_group_document (group_id);
-- Creating an index on document_id to improve query performance when filtering by document_id
CREATE INDEX idx_document_id ON shared_group_document (document_id);


CREATE OR REPLACE FUNCTION delete_related_shared_document_entries()
    RETURNS TRIGGER AS
$$
BEGIN
    -- Delete rows from langchain_pg_embedding where cmetadata->>'blob_id' matches the deleted blob_id
    DELETE
    FROM shared_group_document
    WHERE group_id = OLD.id;

    -- Return the OLD row (standard for AFTER DELETE triggers)
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_shared_document_delete_trigger
    AFTER DELETE
    ON shared_group_document
    FOR EACH ROW
EXECUTE FUNCTION delete_related_shared_document_entries();
