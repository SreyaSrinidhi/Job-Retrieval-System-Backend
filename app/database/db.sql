BEGIN;

-- RESUMES
CREATE TABLE IF NOT EXISTS resumes (
    id              BIGSERIAL PRIMARY KEY,

    -- Raw resume text extracted
    resume_text     TEXT NOT NULL,

    -- Optional metadata ?
    filename        TEXT,
    file_url        TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON resumes(created_at DESC);

-- RESUME EXTRACTIONS (LLM OUTPUT)
-- Stores structured data extracted from a resume (skills, titles, etc.).
CREATE TABLE IF NOT EXISTS resume_extractions (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,

    -- e.g. {"skills":["python","sql"], "titles":["data analyst"], ...}
    extracted_json  JSONB NOT NULL,

    model_name      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resume_extractions_resume_id
ON resume_extractions(resume_id);

-- JOBS (RemoteOK now, supports other sources later)
CREATE TABLE IF NOT EXISTS jobs (
    id              BIGSERIAL PRIMARY KEY,

    source          TEXT NOT NULL,
    source_job_id   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    -- Core fields
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,

    -- URLs
    url             TEXT NOT NULL,
    apply_url        TEXT,

    -- RemoteOK extras
    slug            TEXT,
    company_logo    TEXT,
    tags            JSONB,
    description     TEXT,
    date_posted     TIMESTAMPTZ,
    epoch           BIGINT,
    salary_min      INTEGER,
    salary_max      INTEGER,

    -- Lifecycle tracking (even with hard delete, this is useful for debugging)
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicates per source
    CONSTRAINT uq_jobs_source_source_job_id UNIQUE (source, source_job_id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_date_posted ON jobs(date_posted DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at ON jobs(last_seen_at DESC);

-- MATCHES
-- Stores resume->job match score + explanation
CREATE TABLE IF NOT EXISTS matches (
    id              BIGSERIAL PRIMARY KEY,

    resume_id       BIGINT NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    job_id          BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    score           DOUBLE PRECISION NOT NULL,
    explanation     TEXT,
    metadata        JSONB,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_matches_resume_job UNIQUE (resume_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_resume_id ON matches(resume_id);
CREATE INDEX IF NOT EXISTS idx_matches_job_id ON matches(job_id);
CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(score DESC);

COMMIT;