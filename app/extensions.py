from psycopg_pool import ConnectionPool
from google import genai


"""
A class to encapsulate API and DB extensions and connections for the Flask application.
To be initialized run_app() within __init__.py, and then importable throughout the scope of the app.
"""

class Extensions:
    db_pool: ConnectionPool
    llm_client: genai.Client

    #safe getter method for db_pool - errors if attempting to access before initialization
    def get_db_pool(self) -> ConnectionPool:
        if self.db_pool == None:
            raise RuntimeError("Attempted to access db_pool before initialization")
        
        return self.db_pool
    
    def get_llm_client(self) -> genai.Client:
        if self.llm_client == None:
            raise RuntimeError("Attempted to access llm_client before initialization")
        
        return self.llm_client

extensions = Extensions()