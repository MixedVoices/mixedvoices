# test_db.py
import mixedvoices
import time

def test_database():
    # Create a project with timestamp to ensure uniqueness
    project_name = f"test_project_{int(time.time())}"
    print(f"\nCreating project: {project_name}")
    
    project = mixedvoices.create_project(project_name)
    print(f"Created project with ID: {project.id}")
    
    # Verify we can read it back
    print("\nReading all projects...")
    db = mixedvoices.db.Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects")
            projects = cur.fetchall()
            for p in projects:
                print(f"Found project: {p}")

if __name__ == "__main__":
    test_database()