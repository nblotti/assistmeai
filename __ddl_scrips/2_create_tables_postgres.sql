------------------------------------------------------------------------------------------------------------------------
-- document & category
CREATE TABLE document
(
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255),
    created_on  TIMESTAMP DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    owner VARCHAR(255),
    perimeter VARCHAR(255),
    summary     numeric,
    summary_status  VARCHAR(255) NOT NULL DEFAULT 'NONE',
    document_type VARCHAR(255) NOT NULL DEFAULT 'SUMMARY',
    document    BYTEA
);

CREATE SEQUENCE owner_sequence;

CREATE TABLE document_category
(
    id            INT DEFAULT nextval('owner_sequence') PRIMARY KEY,
    category_name TEXT UNIQUE
);
------------------------------------------------------------------------------------------------------------------------
-- conversation
CREATE TABLE conversation
(
    id          SERIAL PRIMARY KEY, -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    perimeter   VARCHAR(255),
    document_id numeric      DEFAULT 0,
    description VARCHAR(255) DEFAULT 'New chat',
    created_on  TIMESTAMP    DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY')
);

-- Create the trigger function
CREATE OR REPLACE FUNCTION delete_related_conversations()
    RETURNS TRIGGER AS
$$
BEGIN
    DELETE FROM conversation WHERE document_id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER delete_conversations_trigger
    AFTER DELETE
    ON document
    FOR EACH ROW
EXECUTE FUNCTION delete_related_conversations();

CREATE TABLE message
(
    id              SERIAL PRIMARY KEY, -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    conversation_id INTEGER,
    role            TEXT,
    content         TEXT,
    created_on      TIMESTAMP DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    FOREIGN KEY (conversation_id) REFERENCES conversation (id) ON DELETE CASCADE
);


------------------------------------------------------------------------------------------------------------------------
-- assistants

CREATE TABLE assistants
(
    id               SERIAL PRIMARY KEY, -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    user_id          TEXT,
    conversation_id  INTEGER,
    name             TEXT,
    description      TEXT,
    gpt_model_number TEXT DEFAULT '3.5'-- Adding the model_number column at the end
);
CREATE OR REPLACE FUNCTION delete_related_conversation()
    RETURNS TRIGGER AS
$$
BEGIN
    DELETE
    FROM conversation
    WHERE id = OLD.conversation_id;

    -- Return the OLD row (standard for AFTER DELETE triggers)
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger
CREATE TRIGGER after_delete_assistant_trigger
    AFTER DELETE
    ON assistants
    FOR EACH ROW
EXECUTE FUNCTION delete_related_conversation();

------------------------------------------------------------------------------------------------------------------------
-- rights

CREATE TABLE user_groups
(
    id          SERIAL PRIMARY KEY, -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    group_id    TEXT,
    category_id INTEGER,
    UNIQUE (group_id, category_id),
    FOREIGN KEY (category_id) REFERENCES document_category (id) ON DELETE CASCADE
);

create view category_by_group as
select ug.group_id, ug.category_id, dc.category_name
from user_groups ug,
     document_category dc
where ug.category_id = dc.id;

------------------------------------------------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;

CREATE OR REPLACE FUNCTION delete_related_entries()
    RETURNS TRIGGER AS
$$
BEGIN
    -- Delete rows from langchain_pg_embedding where cmetadata->>'blob_id' matches the deleted blob_id
    DELETE
    FROM langchain_pg_embedding
    WHERE cmetadata ->> 'blob_id' = OLD.id::text;

    -- Return the OLD row (standard for AFTER DELETE triggers)
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger
CREATE TRIGGER after_delete_trigger
    AFTER DELETE
    ON document
    FOR EACH ROW
EXECUTE FUNCTION delete_related_entries();

------------------------------------------------------------------------------------------------------------------------

-- Indexes for document table
CREATE INDEX idx_document_name ON document (name);
CREATE INDEX idx_document_created_on ON document (created_on);
CREATE INDEX idx_document_owner ON document (owner);

-- Indexes for document_category table
CREATE INDEX idx_category_name ON document_category (category_name);

-- Indexes for conversation table
CREATE INDEX idx_conversation_document_id ON conversation (document_id);
CREATE INDEX idx_conversation_created_on ON conversation (created_on);

-- Indexes for message table
CREATE INDEX idx_message_conversation_id ON message (conversation_id);
CREATE INDEX idx_message_created_on ON message (created_on);

-- Indexes for assistants table
CREATE INDEX idx_assistants_user_id ON assistants (user_id);
CREATE INDEX idx_assistants_conversation_id ON assistants (conversation_id);

-- Indexes for user_groups table
CREATE INDEX idx_user_groups_group_id ON user_groups (group_id);
CREATE INDEX idx_user_groups_category_id ON user_groups (category_id);




