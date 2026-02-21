from typing import Any
from app.extensions import extensions
from psycopg.rows import dict_row


#function to list all jobs on the database
def list_jobs(jobs_limit: int) -> list[dict[str, Any]]:
    jobs_limit = max(1, min(jobs_limit, 50))

    with extensions.get_db_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, title, company, location, url, description, source, created_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (jobs_limit,),
            )
            rows = cur.fetchall()

    for r in rows:
        if r["created_at"]:
            r["created_at"] = r["created_at"].isoformat()

    return rows