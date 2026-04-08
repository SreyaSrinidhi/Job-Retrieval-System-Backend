from services.embedding_service import compare_texts

resume = "Skills: Cardiology, Patient Care, Clinical Research, Role: Cardiologist, Experience: Diagnosed and treated heart conditions"

jobs = [
    "Backend Java engineer",
    "Data scientist with Python and ML experience",
    "Frontend React developer",
    "Machine learning engineer with Python and data pipelines"
]

for job in jobs:
    score = compare_texts(resume, job)
    print(f"Similarity Score: {score}")