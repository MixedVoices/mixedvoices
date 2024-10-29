# manage.py
import argparse
from mixedvoices.db import Database
import os
import sys

def check_docker():
    """Check if Docker containers are running"""
    import subprocess
    try:
        output = subprocess.check_output(['docker-compose', 'ps'], stderr=subprocess.STDOUT)
        return b'Up' in output
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Manage MixedVoices application')
    parser.add_argument('command', choices=['init', 'reset', 'status'])
    
    args = parser.parse_args()
    
    if args.command == 'status':
        print("Checking system status...")
        docker_running = check_docker()
        print(f"Docker containers: {'Running' if docker_running else 'Not running'}")
        
        try:
            db = Database()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM projects")
                    project_count = cur.fetchone()[0]
                    print(f"Database connection: Success")
                    print(f"Total projects: {project_count}")
        except Exception as e:
            print(f"Database connection: Failed ({str(e)})")
            
    elif args.command == 'init':
        print("Initializing database...")
        db = Database()
        db.init_db()
        
    elif args.command == 'reset':
        print("Resetting database...")
        try:
            db = Database()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DROP TABLE IF EXISTS processing_results CASCADE;
                        DROP TABLE IF EXISTS recordings CASCADE;
                        DROP TABLE IF EXISTS versions CASCADE;
                        DROP TABLE IF EXISTS projects CASCADE;
                    """)
                    conn.commit()
            db.init_db()
            print("Database reset successfully!")
        except Exception as e:
            print(f"Error resetting database: {str(e)}")

if __name__ == "__main__":
    main()