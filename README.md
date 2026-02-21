# Job Retrieval System Backend - Flask App

**Site URL:** https://job-retrieval-system-backend.onrender.com/

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
python run.py
```

## Project Organization

 - The Flask application root runs from `run.py`.

 - The core functionality of the application is defined with the `./app` module. The file `./app/__init__.py` defines the **create_app()** function, which initializes the application. The file `./app/extensions.py` defines an importable object to hold connections such as LLM API Client or DB Connection Pool.

 - Routes are defined in `./app/routes`. This directory should ONLY handle request I/O, not backend processing or API calls.

 - Services are defined in `./app/services`, and handle all backend processing logic.

 - Database SQL is contained in `./app/database`.

## Development Guidelines

### Adding New Routes

New routes are to be added in the `./app/routes` module using Flask Blueprints. Each Blueprint file encompasses a set of similar routes (eg database_queries blueprint holds all routes that are meant to query the database).

To add a new route to an existing Blueprint, use the following syntax

```python
@<blueprint_name>.route("/<route_extension>", methods=["<method_type (eg GET, POST, etc)"])
```

To create a new Blueprint, make a new file in `./app/routes` and initialize the Blueprint with its constructor. Then, to add the Blueprint's routes to the Flask application's path, import the new Blueprint object in `./app/__init__.py` and add it with the syntax

```python
app.register_blueprint(<blueprint_name>, url_prefix="/<route_prefix>")
```

### Accessing Extensions

`./app/extensions.py` defines an **Extensions()** object which is initialized in `./app/__init__.py`. The extensions object should make available all persistent API or Database connection objects.

To access these objects anywhere within `./app/*`, import extensions from app.extensions, and access any field of the extensions object.