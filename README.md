# Job Retrieval System Backend - Flask App


## Setup

### 1. Clone the repository:

```bash
git clone https://github.com/SreyaSrinidhi/Job-Retrieval-System-Backend.git
cd Job-Retrieval-System-Backend
```

### 2. Create a virtual environment:

```bash
python -m venv venv
```

or 

```bash
python3.11 -m venv venv
```

### 3. Activate the virtual environment:

 - Linux/macOS: `source venv/bin/activate`
 - Windows (PowerShell): `venv\Scripts\Activate`

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

This project requires a Gemini API key to call the LLM. To keep your key secure:
1. Create a file named .env in the **project root** (same folder as `app.py`).
2. Add your API key like this:
```bash
GEMINI_API_KEY=your_api_key_here
DATABASE_URL="paste-your-external-database-url-here"
```
**Important Note**: Do NOT commit the `.env` file to GitHub. It is already in the .gitignore

3. The app will automatically load this key using `python-dotenv`

### 6 Running the Flask App

```bash
python app.py
```
