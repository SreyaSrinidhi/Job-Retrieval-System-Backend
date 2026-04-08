from services.embedding_service import compare_texts

resume = "Software Engineer"

jobs = [
    "Backend Java engineer",
    "Data scientist with Python and ML experience",
    "Frontend React developer",
    "Machine learning engineer with Python and data pipelines"
]

for job in jobs:
    score = compare_texts(resume, job)
    print(f"Similarity Score: {score}")