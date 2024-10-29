# start_db.py
from mixedvoices.db import Database

def setup_database():
    try:
        db = Database()
        db.init_db()
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database()