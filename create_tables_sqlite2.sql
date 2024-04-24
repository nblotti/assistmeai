CREATE TABLE pdf (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    user VARCHAR(255),
    document BYTEA
);

create table message(
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    created_on DATETIME
 );