from typing import Any, Dict, List, Optional, Tuple
from app.extensions import extensions
from psycopg.rows import dict_row
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import requests
import hashlib
import re

import requests

from app.extensions import extensions


#function to list all jobs on the database
def list_jobs(jobs_limit: Optional[int] = None) -> list[dict[str, Any]]:
    with extensions.get_db_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if jobs_limit is None:
                cur.execute(
                    """
                    SELECT
                        id, source, source_job_id, is_active,
                        title, company, location,
                        url, apply_url, slug, company_logo,
                        tags, description, date_posted, epoch, salary_min, salary_max,
                        last_seen_at, created_at, updated_at
                    FROM jobs
                    ORDER BY COALESCE(date_posted, created_at) DESC
                    """
                )
            else:
                jobs_limit = max(1, jobs_limit)
                cur.execute(
                    """
                    SELECT
                        id, source, source_job_id, is_active,
                        title, company, location,
                        url, apply_url, slug, company_logo,
                        tags, description, date_posted, epoch, salary_min, salary_max,
                        last_seen_at, created_at, updated_at
                    FROM jobs
                    ORDER BY COALESCE(date_posted, created_at) DESC
                    LIMIT %s
                    """,
                    (jobs_limit,),
                )
            rows = cur.fetchall()

    for r in rows:
        for dt_key in ("date_posted", "last_seen_at", "created_at", "updated_at"):
            if r.get(dt_key):
                r[dt_key] = r[dt_key].isoformat()

    return rows


def get_jobs_payload(limit_raw: Optional[str]) -> tuple[dict[str, Any], int]:
    if limit_raw is None:
        limit = None
    else:
        try:
            limit = int(limit_raw)
        except ValueError:
            return {"status": "error", "message": "limit must be an integer"}, 400

    jobs = list_jobs(limit)
    return {"count": len(jobs), "jobs": jobs}, 200

#-------------------Service functions for syncing RemoteOK and SimplifyJobs----------------------------

# --------- RemoteOK API ---------
REMOTEOK_API_URL: str = "https://remoteok.com/api"

@dataclass(frozen=True)
class RemoteOkJob:
    """Normalized job record from RemoteOK."""
    source: str
    source_job_id: str
    title: str
    company: str
    location: Optional[str]
    url: str
    apply_url: Optional[str]
    slug: Optional[str]
    company_logo: Optional[str]
    tags: List[str]
    description: Optional[str]
    date_posted: Optional[datetime]
    epoch: Optional[int]
    salary_min: Optional[int]
    salary_max: Optional[int]


def _parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    RemoteOK returns ISO strings like: '2026-02-23T00:00:20+00:00'
    Convert to aware datetime. Return None if missing/invalid.
    """
    if not dt_str:
        return None
    try:
        # fromisoformat handles "+00:00" offsets
        dt = datetime.fromisoformat(dt_str)
        # ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def fetch_remoteok_jobs(limit: int = 1000) -> List[RemoteOkJob]:
    """
    Fetch jobs from RemoteOK, normalize fields, sort newest first, cap at 'limit'.
    """
    resp = requests.get(
        REMOTEOK_API_URL,
        headers={"User-Agent": "CWRU-Capstone-JobFetcher/1.0"},
        timeout=30,
    )
    resp.raise_for_status()
    data: Any = resp.json()

    if not isinstance(data, list):
        raise RuntimeError("Unexpected RemoteOK API response format (expected list).")

    jobs: List[RemoteOkJob] = []

    for item in data:
        # The first element often contains metadata/legal info, not a job record.
        if not isinstance(item, dict):
            continue
        if "id" not in item or "position" not in item or "company" not in item or "url" not in item:
            continue

        tags_val = item.get("tags") or []
        if not isinstance(tags_val, list):
            tags_val = []

        job = RemoteOkJob(
            source="remoteok",
            source_job_id=str(item.get("id")),
            title=str(item.get("position") or "").strip(),
            company=str(item.get("company") or "").strip(),
            location=(str(item.get("location")).strip() if item.get("location") else None),
            url=str(item.get("url") or "").strip(),
            apply_url=(str(item.get("apply_url")).strip() if item.get("apply_url") else None),
            slug=(str(item.get("slug")).strip() if item.get("slug") else None),
            company_logo=(str(item.get("company_logo")).strip() if item.get("company_logo") else None),
            tags=[str(t).strip() for t in tags_val if str(t).strip()],
            description=(str(item.get("description")) if item.get("description") else None),
            date_posted=_parse_iso_datetime(item.get("date")),
            epoch=(int(item["epoch"]) if isinstance(item.get("epoch"), (int, float, str)) and str(item.get("epoch")).isdigit() else None),
            salary_min=(int(item["salary_min"]) if isinstance(item.get("salary_min"), (int, float)) else None),
            salary_max=(int(item["salary_max"]) if isinstance(item.get("salary_max"), (int, float)) else None),
        )

        # Basic sanity checks: title/company/url must exist
        if not job.title or not job.company or not job.url or not job.source_job_id:
            continue

        jobs.append(job)

    # Sort by epoch if present, else by date_posted, else push to bottom
    def sort_key(j: RemoteOkJob) -> int:
        if j.epoch is not None:
            return j.epoch
        if j.date_posted is not None:
            return int(j.date_posted.timestamp())
        return 0

    jobs.sort(key=sort_key, reverse=True)

    # Cap results
    return jobs[: max(0, int(limit))]

def sync_remoteok_jobs(limit: int = 1000, inactive_after_days: int = 10) -> Dict[str, int]:
    """
    Sync RemoteOK jobs into the DB without deleting history.

    - Upsert jobs seen in this fetch:
        set is_active = TRUE, last_seen_at = NOW(), update core fields
    - Mark jobs inactive if not seen for `inactive_after_days`.
    """
    jobs = fetch_remoteok_jobs(limit=limit)
    pool = extensions.get_db_pool()

    upsert_sql = """
        INSERT INTO jobs (
            source, source_job_id,
            title, company, location,
            url, apply_url, slug, company_logo,
            tags, description,
            date_posted, epoch, salary_min, salary_max,
            is_active, last_seen_at,
            created_at, updated_at
        )
        VALUES (
            %(source)s, %(source_job_id)s,
            %(title)s, %(company)s, %(location)s,
            %(url)s, %(apply_url)s, %(slug)s, %(company_logo)s,
            %(tags)s::jsonb, %(description)s,
            %(date_posted)s, %(epoch)s, %(salary_min)s, %(salary_max)s,
            TRUE, NOW(),
            NOW(), NOW()
        )
        ON CONFLICT (source, source_job_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            url = EXCLUDED.url,
            apply_url = EXCLUDED.apply_url,
            slug = EXCLUDED.slug,
            company_logo = EXCLUDED.company_logo,
            tags = EXCLUDED.tags,
            description = EXCLUDED.description,
            date_posted = EXCLUDED.date_posted,
            epoch = EXCLUDED.epoch,
            salary_min = EXCLUDED.salary_min,
            salary_max = EXCLUDED.salary_max,
            is_active = TRUE,
            last_seen_at = NOW(),
            updated_at = NOW();
    """

    deactivate_sql = """
        UPDATE jobs
        SET is_active = FALSE,
            updated_at = NOW()
        WHERE source = 'remoteok'
          AND last_seen_at < NOW() - (%s || ' days')::interval;
    """

    rows: List[Dict[str, Any]] = []
    for j in jobs:
        rows.append(
            {
                "source": j.source,
                "source_job_id": j.source_job_id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "apply_url": j.apply_url,
                "slug": j.slug,
                "company_logo": j.company_logo,
                "tags": json.dumps(j.tags),
                "description": j.description,
                "date_posted": j.date_posted,
                "epoch": j.epoch,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
            }
        )

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            try:
                upserted = 0
                if rows:
                    cur.executemany(upsert_sql, rows)
                    upserted = len(rows)

                cur.execute(deactivate_sql, (inactive_after_days,))
                deactivated = cur.rowcount

                cur.execute("COMMIT;")
            except Exception:
                cur.execute("ROLLBACK;")
                raise

    return {"fetched": len(rows), "upserted": upserted, "deactivated": deactivated}

# --------- SimplifyJobs New Grad ---------

SIMPLIFY_REPO_OWNER: str = "SimplifyJobs"
SIMPLIFY_REPO_NAME: str = "New-Grad-Positions"
SIMPLIFY_REF: str = "dev"

SIMPLIFY_RAW_ROOT_README: str = (
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"
)

# GitHub REST (no auth) - used to list /archived files dynamically
GITHUB_CONTENTS_ARCHIVED_URL: str = (
    "https://api.github.com/repos/SimplifyJobs/New-Grad-Positions/contents/archived?ref=dev"
)


@dataclass(frozen=True)
class SimplifyJob:
    source: str
    source_job_id: str
    title: str
    company: str
    location: Optional[str]
    url: str
    apply_url: Optional[str]
    tags: List[str]
    date_posted: Optional[datetime]

# The SimplifyJobs repo has a unique format where jobs are listed in markdown tables across the root README and archived files. The following functions handle fetching, parsing, and syncing these jobs into our database.
def _clean_md_cell(cell: str) -> str:
    s = cell.strip()
    s = s.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Extract markdown links of the form [text](url) from a string. Return list of URLs.
def _extract_all_md_links(text: str) -> List[str]:
    return [m.group(1).strip() for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text)]

# Extract the first markdown link URL from a string, or None if no links found.
def _extract_first_md_link(text: str) -> Optional[str]:
    links = _extract_all_md_links(text)
    return links[0] if links else None

# Convert Simplify 'Age' strings like "3d", "1w", "2mo" to approximate posted date. Return None if unparseable.
def _parse_age_to_date_posted(age_str: str) -> Optional[datetime]:
    """
    Convert Simplify 'Age' to approximate posted date.
    Examples: 0d, 3d, 1w, 2mo
    """
    s = age_str.strip().lower()
    now = datetime.now(timezone.utc)

    m = re.match(r"^(\d+)\s*d$", s)
    if m:
        return now - timedelta(days=int(m.group(1)))

    m = re.match(r"^(\d+)\s*w$", s)
    if m:
        return now - timedelta(days=7 * int(m.group(1)))

    m = re.match(r"^(\d+)\s*mo$", s)
    if m:
        return now - timedelta(days=30 * int(m.group(1)))

    return None

# Helper to fetch markdown text from a URL with retries and error handling.
def _requests_get_text(url: str, timeout_s: int = 30) -> str:
    resp = requests.get(
        url,
        headers={
            "User-Agent": "CWRU-Capstone-JobFetcher/1.0",
            "Accept": "text/plain, text/markdown, */*",
        },
        timeout=timeout_s,
    )
    resp.raise_for_status()
    return resp.text

def fetch_simplify_markdown_sources() -> List[Tuple[str, str]]:
    """
    Fetch ALL markdown sources containing listings:
      - root README.md (dev)
      - every archived/*.md discovered via GitHub contents API (dev)
    Returns list of (name, markdown_text).
    """
    sources: List[Tuple[str, str]] = []

    # 1) Root README
    root_md = _requests_get_text(SIMPLIFY_RAW_ROOT_README)
    sources.append(("README.md", root_md))

    # 2) Discover archived READMEs using GitHub API
    try:
        data = requests.get(
            GITHUB_CONTENTS_ARCHIVED_URL,
            headers={"User-Agent": "CWRU-Capstone-JobFetcher/1.0", "Accept": "application/json"},
            timeout=30,
        )
        data.raise_for_status()
        items: Any = data.json()

        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                # only markdown files
                if not name.lower().endswith(".md"):
                    continue
                # prefer README-like archived files
                if "readme" not in name.lower():
                    continue

                download_url = item.get("download_url")
                if isinstance(download_url, str) and download_url:
                    md = _requests_get_text(download_url)
                    sources.append((f"archived/{name}", md))
    except Exception:
        # If GitHub contents API fails (rate limit etc.), we still have root README.
        pass

    return sources


def parse_simplify_jobs_from_markdown(readme_md: str, max_jobs: int = 100000) -> List[SimplifyJob]:
    """
    Parse one markdown file. Extract all category tables.

    Expected table columns:
      | Company | Role | Location | Application | Age |
    """
    lines = readme_md.splitlines()
    jobs: List[SimplifyJob] = []

    category: Optional[str] = None
    last_company: Optional[str] = None
    last_company_url: Optional[str] = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Category header (works for common headings in the repo)
        m = re.match(r"^##\s+(.*?)(?:\s+New\s+Grad\s+Roles)?\s*$", line, flags=re.IGNORECASE)
        if m:
            possible = m.group(1).strip()
            # Skip generic headings that are not categories
            if possible and "table of contents" not in possible.lower():
                category = possible
                last_company = None
                last_company_url = None
            i += 1
            continue

        # Table header
        if line.startswith("|") and "Company" in line and "Role" in line and "Location" in line and "Application" in line:
            # Skip separator line
            i += 2

            while i < len(lines):
                row = lines[i].rstrip()
                if not row.strip().startswith("|"):
                    break

                parts = [p.strip() for p in row.split("|")[1:-1]]
                i += 1

                if len(parts) < 5:
                    continue

                company_cell, role_cell, location_cell, app_cell, age_cell = parts[:5]

                # Handle sub-rows that begin with ↳ (inherit company)
                company_text = _clean_md_cell(company_cell)
                if company_text.startswith("↳") or company_text == "":
                    if last_company is None:
                        continue
                    company = last_company
                    company_url = last_company_url
                    title = _clean_md_cell(_clean_md_cell(role_cell))
                else:
                    company = _clean_md_cell(re.sub(r"^↳\s*", "", company_text))
                    company_url = _extract_first_md_link(company_cell)
                    last_company = company
                    last_company_url = company_url
                    title = _clean_md_cell(role_cell)

                location = _clean_md_cell(location_cell) or None

                links = _extract_all_md_links(app_cell)

                # Prefer non-simplify.jobs as apply_url if present
                apply_url: Optional[str] = None
                for u in links:
                    if "simplify.jobs" not in u:
                        apply_url = u
                        break
                if apply_url is None and links:
                    apply_url = links[0]

                # url must be NOT NULL per your schema
                # Prefer company/simplify posting link if present, else fallback to apply_url
                url = company_url or apply_url
                if not url:
                    continue

                date_posted = _parse_age_to_date_posted(_clean_md_cell(age_cell))

                # Stable ID from URL (or fallback)
                stable_key = url or f"{company}|{title}|{location or ''}|{category or ''}"
                source_job_id = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()

                tags: List[str] = ["newgrad"]
                if category:
                    tags.append(f"category:{category}")

                jobs.append(
                    SimplifyJob(
                        source="simplify_newgrad",
                        source_job_id=source_job_id,
                        title=title,
                        company=company,
                        location=location,
                        url=url,
                        apply_url=apply_url,
                        tags=tags,
                        date_posted=date_posted,
                    )
                )

                if len(jobs) >= max_jobs:
                    return jobs

            continue

        i += 1

    return jobs


def sync_simplify_jobs(limit: int = 1000, inactive_after_days: int = 10) -> Dict[str, int]:
    """
    Sync SimplifyJobs across README + archived READMEs.

    - Fetch all markdown sources
    - Parse all jobs
    - Deduplicate by source_job_id (stable hash)
    - Upsert all (or capped) jobs into DB
    - Mark inactive any simplify jobs not seen for inactive_after_days
    """
    sources = fetch_simplify_markdown_sources()

    # Parse all files
    all_jobs: List[SimplifyJob] = []
    for name, md in sources:
        all_jobs.extend(parse_simplify_jobs_from_markdown(md))

    # Deduplicate by source_job_id (same job can appear in multiple files)
    dedup: Dict[str, SimplifyJob] = {}
    for j in all_jobs:
        dedup[j.source_job_id] = j

    jobs_unique = list(dedup.values())

    # Prefer more recent first (date_posted/age is approximate, but useful)
    def sort_key(j: SimplifyJob) -> int:
        if j.date_posted is not None:
            return int(j.date_posted.timestamp())
        return 0

    jobs_unique.sort(key=sort_key, reverse=True)

    # Cap insert if requested
    cap = max(1, min(limit, 50000))
    jobs_unique = jobs_unique[:cap]

    pool = extensions.get_db_pool()

    upsert_sql = """
        INSERT INTO jobs (
            source, source_job_id, is_active,
            title, company, location,
            url, apply_url,
            tags, description,
            date_posted, epoch, salary_min, salary_max,
            last_seen_at, created_at, updated_at
        )
        VALUES (
            %(source)s, %(source_job_id)s, TRUE,
            %(title)s, %(company)s, %(location)s,
            %(url)s, %(apply_url)s,
            %(tags)s::jsonb, NULL,
            %(date_posted)s, NULL, NULL, NULL,
            NOW(), NOW(), NOW()
        )
        ON CONFLICT (source, source_job_id)
        DO UPDATE SET
            is_active = TRUE,
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            url = EXCLUDED.url,
            apply_url = EXCLUDED.apply_url,
            tags = EXCLUDED.tags,
            date_posted = EXCLUDED.date_posted,
            last_seen_at = NOW(),
            updated_at = NOW();
    """

    deactivate_sql = """
        UPDATE jobs
        SET is_active = FALSE,
            updated_at = NOW()
        WHERE source = 'simplify_newgrad'
          AND last_seen_at < NOW() - (%s || ' days')::interval;
    """

    rows: List[Dict[str, Any]] = []
    for j in jobs_unique:
        rows.append(
            {
                "source": j.source,
                "source_job_id": j.source_job_id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "apply_url": j.apply_url,
                "tags": json.dumps(j.tags),
                "date_posted": j.date_posted,
            }
        )

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN;")
            try:
                if rows:
                    cur.executemany(upsert_sql, rows)

                cur.execute(deactivate_sql, (inactive_after_days,))
                deactivated = cur.rowcount
                cur.execute("COMMIT;")
            except Exception:
                cur.execute("ROLLBACK;")
                raise

    return {
        "sources": len(sources),
        "parsed_total": len(all_jobs),
        "unique": len(dedup),
        "upserted": len(rows),
        "deactivated": deactivated,
    }
