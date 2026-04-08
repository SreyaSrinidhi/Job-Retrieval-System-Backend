from app import create_app  # adjust if needed
from app.services.database_service import list_active_jobs_for_matching
from app.services.embedding_service import embed_text, build_job_embedding_text
from app.extensions import extensions

def run():
    app = create_app()

    jobs = list_active_jobs_for_matching()

    print(f"Found {len(jobs)} jobs")

    for i, job in enumerate(jobs[:10]):
        text = build_job_embedding_text(job)
        embedding = embed_text(text)

        print(f"[{i+1}] {job['title']} → embedding length: {len(embedding)}")
    
    extensions.get_db_pool().close()


if __name__ == "__main__":
    run()