CREATE TABLE jobs
(
    id                 SERIAL PRIMARY KEY,
    source             VARCHAR(255) NOT NULL,
    job_type           VARCHAR(255) NOT NULL DEFAULT 'SUMMARY',
    target_document_id INTEGER,
    owner              VARCHAR(255) NOT NULL,
    status             VARCHAR(255) NOT NULL DEFAULT 'REQUESTED',
    created_on         TIMESTAMP    NOT NULL DEFAULT TO_TIMESTAMP(TO_CHAR(CURRENT_TIMESTAMP, 'DD.MM.YYYY'), 'DD.MM.YYYY'),
    last_update        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NULL
);


CREATE INDEX idx_document_created_on ON jobs (created_on);
CREATE INDEX idx_document_status_owner ON jobs (status, owner);

CREATE OR REPLACE FUNCTION update_job_status() RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.job_type = 'LONG_EMBEDDINGS' THEN
        -- Update the document_status in the document table where the source matches the updated job id
        UPDATE document
        SET document_status = NEW.status
        WHERE id::text = NEW.source;
    ELSIF NEW.job_type = 'SUMMARY' THEN
            -- Update the summary_status in the document table where the source matches the updated job id
            UPDATE document
            SET summary_status = NEW.status,
                summary_id     = NEW.target_document_id
            WHERE id::text = NEW.source;
        END IF;

        -- Return the NEW row (standard for AFTER UPDATE triggers)
        RETURN NEW;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION remove_job_status() RETURNS TRIGGER AS
$$
BEGIN
    -- Update the summary_status in the document table where the source matches the updated job id
    UPDATE document
    SET summary_status = 'NONE',
        summary_id     = null
    WHERE id::text = NEW.source
      AND NEW.job_type != 'LONG_EMBEDDINGS'
      AND NEW.job_type != 'SHARE';

    -- Return the NEW row (standard for AFTER UPDATE triggers)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Create the trigger to call the function after an update on the jobs table
CREATE TRIGGER after_job_update_trigger
    AFTER UPDATE
    ON jobs
    FOR EACH ROW
EXECUTE FUNCTION update_job_status();

CREATE TRIGGER after_job_insert_trigger
    AFTER INSERT
    ON jobs
    FOR EACH ROW
EXECUTE FUNCTION update_job_status();

CREATE TRIGGER after_job_delete_trigger
    AFTER DELETE
    ON jobs
    FOR EACH ROW
EXECUTE FUNCTION remove_job_status();

CREATE OR REPLACE FUNCTION add_embedding_job_() RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.document_type = 'DOCUMENT' THEN
        INSERT INTO jobs (source, job_type, owner, status)
        VALUES (NEW.id, 'LONG_EMBEDDINGS', NEW.owner, 'REQUESTED');
    END IF;

    -- Return the NEW row (standard for AFTER INSERT triggers)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER add_embedding_job_trigger
    AFTER INSERT
    ON document
    FOR EACH ROW
EXECUTE FUNCTION add_embedding_job_();