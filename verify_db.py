# verify_db.py
from mixedvoices.db import Database
from tabulate import tabulate

def verify_database():
    db = Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Get projects
            cur.execute("SELECT * FROM projects")
            projects = cur.fetchall()
            
            # Get column names
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projects'
                ORDER BY ordinal_position
            """)
            columns = [col[0] for col in cur.fetchall()]
            
            print("\nProjects Table:")
            print(tabulate(projects, headers=columns, tablefmt="psql"))
            
            # Show connection info
            cur.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db_info = cur.fetchone()
            print("\nDatabase Connection Info:")
            print(f"Database: {db_info[0]}")
            print(f"User: {db_info[1]}")
            print(f"Server: {db_info[2]}:{db_info[3]}")

if __name__ == "__main__":
    verify_database()