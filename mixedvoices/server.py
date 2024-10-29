# mixedvoices/server.py
from flask import Flask, request, jsonify
import time
import threading
from .db import Database
import os

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'postgresql://admin:postgres@localhost/mixedvoices')
db = Database(connection_string=database_url)

def process_recording(recording_id):
    """Dummy processing function that runs for 2 seconds"""
    time.sleep(2)
    
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO processing_results (recording_id, dummy1, dummy2)
                VALUES (%s, %s, %s)
            """, (recording_id, "dummy_value_1", "dummy_value_2"))
            conn.commit()

@app.route('/process_recording', methods=['POST'])
def handle_recording():
    recording_id = request.json.get('recording_id')
    # Start processing in background
    threading.Thread(target=process_recording, args=(recording_id,)).start()
    return jsonify({"status": "processing"}), 200

# Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Create a run_server.py file in the root directory