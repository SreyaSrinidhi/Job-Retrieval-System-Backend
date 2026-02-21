import os
from dotenv import load_dotenv
from flask import Flask
from google import genai
from psycopg_pool import ConnectionPool
from app.extensions import extensions

from app.routes.health import health_bp
from app.routes.llm import llm_bp
from app.routes.database_queries import database_bp
from app.routes.files import files_bp

#factory function to create app with all blueprint routes registered
def create_app() -> Flask:
    #load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    # Increase maximum upload size to 150 MB
    app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024

    @app.route("/")
    def home():
        print("Flask Application Running!")
        return "Flask Application Running!"

    #------------initialize extensions--------------------------------
    # Note: this can be accessed anywhere in flask by importing app.extensions object

    # #initialize gemini client
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    extensions.llm_client = genai.Client(api_key=gemini_api_key)
    
    # #initialize db connection pool
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    
    #connection pool should be better than creating new connection every time we access db
    extensions.db_pool = ConnectionPool(db_url)
    
    
    #---------register route blueprints here--------------------------
    app.register_blueprint(health_bp, url_prefix="/health")
    app.register_blueprint(llm_bp, url_prefix="/llm")
    app.register_blueprint(database_bp, url_prefix="/database")
    app.register_blueprint(files_bp, url_prefix="/files")

    return app