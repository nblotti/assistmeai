CREATE TABLE shared_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    owner VARCHAR NOT NULL,
    creation_date DATE NOT NULL
);

CREATE INDEX ix_groups_id ON shared_groups (id);