CREATE TABLE document (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_on TIMESTAMP DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    "perimeter" VARCHAR(255),  -- "user" is a reserved keyword in PostgreSQL, so it needs to be quoted
    document BYTEA
);

CREATE TABLE message (
    id SERIAL PRIMARY KEY,  -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    created_on TIMESTAMP  DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY')
);

CREATE TABLE conversation (
    id SERIAL PRIMARY KEY,  -- SERIAL is equivalent to AUTO_INCREMENT in MySQL
    perimeter VARCHAR(255),
    document_id numeric,
    description VARCHAR(255) DEFAULT 'New chat',
    created_on TIMESTAMP   DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY')
);
