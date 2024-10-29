# mixedvoices/server.py
from flask import Flask, request, jsonify
from  mixedvoices.db import Database
from mixedvoices.tasks import process_recording
import os

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/mixedvoices')
db = Database(connection_string=database_url)

@app.route('/process_recording', methods=['POST'])
def handle_recording():
    recording_id = request.json.get('recording_id')
    
    # Queue the task
    task = process_recording.delay(recording_id)
    
    return jsonify({
        "status": "processing",
        "task_id": task.id
    }), 200

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check the status of a processing task"""
    task = process_recording.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task.status,
    }
    if task.ready():
        response["result"] = task.get()
    return jsonify(response)

# Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200