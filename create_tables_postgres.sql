CREATE TABLE document (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_on TIMESTAMP DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    "perimeter" VARCHAR(255),  -- "user" is a reserved keyword in PostgreSQL, so it needs to be quoted
    document BYTEA
);

CREATE TABLE message (
    id SERIAL PRIMARY KEY,  -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    conversation_id INTEGER,
    role TEXT,
    content TEXT,
    created_on TIMESTAMP  DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
);

CREATE TABLE conversation (
    id SERIAL PRIMARY KEY,  -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    perimeter VARCHAR(255),
    document_id numeric,
    description VARCHAR(255) DEFAULT 'New chat',
    created_on TIMESTAMP   DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY')
);

-- Create the trigger function
CREATE OR REPLACE FUNCTION delete_related_conversations()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM conversation WHERE document_id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER delete_conversations_trigger
AFTER DELETE ON document
FOR EACH ROW
EXECUTE FUNCTION delete_related_conversations();
