CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT,
  url TEXT UNIQUE,
  description TEXT,
  source TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resumes (
  id BIGSERIAL PRIMARY KEY,
  filename TEXT,
  raw_text TEXT,
  extracted_keywords JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matches (
  id BIGSERIAL PRIMARY KEY,
  resume_id BIGINT NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  score DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (resume_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company_title ON jobs (company, title);
CREATE INDEX IF NOT EXISTS idx_matches_resume ON matches (resume_id);