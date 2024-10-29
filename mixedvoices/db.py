# mixedvoices/db.py
import psycopg2
from psycopg2.extras import Json
import json
import os
import time

class Database:
    def __init__(self, connection_string=None):
        # Try Docker container URL first, then fall back to localhost
        self.conn_string = connection_string or os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/mixedvoices')
        
    def get_connection(self, max_retries=5):
        """Get database connection with retries"""
        last_exception = None
        
        # Try both the Docker container hostname and localhost
        urls = [
            self.conn_string,
            self.conn_string.replace('@db/', '@localhost/'),
            'postgresql://postgres:postgres@localhost/mixedvoices'
        ]
        
        for attempt in range(max_retries):
            for url in urls:
                try:
                    return psycopg2.connect(url)
                except psycopg2.OperationalError as e:
                    last_exception = e
                    time.sleep(1)  # Wait before retrying
        
        print(f"Could not connect to database after {max_retries} attempts.")
        print("Please ensure PostgreSQL is running and the credentials are correct.")
        print("If using Docker, make sure the containers are running with: docker-compose up")
        raise last_exception

    def init_db(self):
        """Initialize database tables and set proper permissions"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create tables
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS versions (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER REFERENCES projects(id),
                        name VARCHAR(255) NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(project_id, name)
                    )
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recordings (
                        id SERIAL PRIMARY KEY,
                        version_id INTEGER REFERENCES versions(id),
                        filename VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS processing_results (
                        id SERIAL PRIMARY KEY,
                        recording_id INTEGER REFERENCES recordings(id),
                        dummy1 VARCHAR(255),
                        dummy2 VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Grant permissions
                cur.execute("""
                    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;
                """)
                
                conn.commit()
                print("Database initialized successfully!")