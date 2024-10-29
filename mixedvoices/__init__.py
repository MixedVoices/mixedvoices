import requests
from mixedvoices.db import Database
from psycopg2.extras import Json


class Recording:
    def __init__(self, id, filename, version_id):
        self.id = id
        self.filename = filename
        self.version_id = version_id

class Version:
    def __init__(self, id, name, project_id, metadata):
        self.id = id
        self.name = name
        self.project_id = project_id
        self.metadata = metadata
        self.db = Database()
        
    def add_recording(self, filename):
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recordings (version_id, filename)
                    VALUES (%s, %s)
                    RETURNING id
                """, (self.id, filename))
                recording_id = cur.fetchone()[0]
                conn.commit()
                
                # Make request to processing server
                requests.post(
                    'http://localhost:5001/process_recording',
                    json={'recording_id': recording_id}
                )
                
                return Recording(recording_id, filename, self.id)

class Project:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.db = Database()
    
    def create_version(self, name, metadata=None):
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO versions (project_id, name, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (self.id, name, Json(metadata) if metadata else None))
                version_id = cur.fetchone()[0]
                conn.commit()
                return Version(version_id, name, self.id, metadata)
    
    def load_version(self, name):
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, metadata FROM versions
                    WHERE project_id = %s AND name = %s
                """, (self.id, name))
                result = cur.fetchone()
                if result:
                    version_id, metadata = result
                    return Version(version_id, name, self.id, metadata)
                raise ValueError(f"Version {name} not found")

def create_project(name):
    db = Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (name)
                VALUES (%s)
                RETURNING id
            """, (name,))
            project_id = cur.fetchone()[0]
            conn.commit()
            return Project(project_id, name)

def load_project(name):
    db = Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM projects
                WHERE name = %s
            """, (name,))
            result = cur.fetchone()
            if result:
                return Project(result[0], name)
            raise ValueError(f"Project {name} not found")