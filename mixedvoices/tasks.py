# mixedvoices/tasks.py
from celery import Celery
from mixedvoices.db import Database
import os
import time

# Configure Celery
celery_app = Celery('mixedvoices',
                    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@celery_app.task
def process_recording(recording_id):
    """Process a recording asynchronously"""
    print(f"Processing recording {recording_id}")
    
    # Simulate CPU/GPU intensive task
    time.sleep(2)
    
    # Update database with results
    db = Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO processing_results (recording_id, dummy1, dummy2)
                VALUES (%s, %s, %s)
            """, (recording_id, "dummy_value_1", "dummy_value_2"))
            conn.commit()
    
    return {"status": "completed", "recording_id": recording_id}