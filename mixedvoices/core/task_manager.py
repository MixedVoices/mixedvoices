import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from typing import Any, Dict, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.utils import load_json, save_json


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    task_id: str
    task_type: str
    params: Dict[str, Any]
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "params": self.params,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class TaskManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.task_queue = Queue()
        self.tasks: Dict[str, Task] = {}
        self.processing_thread = None
        self.monitor_thread = None
        self.is_processing = False

        self.tasks_root = os.path.join(constants.MIXEDVOICES_FOLDER, "_tasks")
        self.create_folders()

        self._load_pending_tasks()
        self._start_processing_thread()
        self._start_monitor_thread()

    def create_folders(self):
        self.folder_paths = {
            TaskStatus.PENDING: os.path.join(self.tasks_root, "pending"),
            TaskStatus.IN_PROGRESS: os.path.join(self.tasks_root, "in_progress"),
            TaskStatus.COMPLETED: os.path.join(self.tasks_root, "completed"),
            TaskStatus.FAILED: os.path.join(self.tasks_root, "failed"),
        }

        for folder in self.folder_paths.values():
            os.makedirs(folder, exist_ok=True)

    def _monitor_status(self):
        main_thread = threading.main_thread()
        status_printed = False

        while True:
            if not main_thread.is_alive():
                if (
                    self.task_queue.qsize() > 0 or self.is_processing
                ) and not status_printed:
                    print(
                        "MixedVoices is still processing recordings. "
                        "In case you want to change this behaviour, "
                        "use blocking=True in add_recording()"
                    )
                    status_printed = True
                elif self.task_queue.qsize() == 0 and not self.is_processing:
                    break
            time.sleep(0.5)

    def _start_monitor_thread(self):
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self._monitor_status, name="TaskMonitorThread"
            )
            self.monitor_thread.start()

    def _serialize_task_params(
        self, task_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert task parameters into JSON-serializable format."""
        if task_type == "process_recording":
            recording = params["recording"]
            version = params["version"]
            return {
                "recording_data": {
                    "recording_id": recording.id,
                    "audio_path": recording.audio_path,
                    "version_id": recording.version_id,
                    "project_id": recording.project_id,
                    "is_successful": recording.is_successful,
                    "metadata": recording.metadata,
                    "summary": recording.summary,
                    "combined_transcript": recording.combined_transcript,
                },
                "version_data": {
                    "version_id": version.id,
                    "project_id": version.project_id,
                },
                "user_channel": params["user_channel"],
            }
        return params

    def _deserialize_task_params(
        self, task_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert serialized parameters back into required objects."""
        if task_type != "process_recording":
            return params
        from mixedvoices.core.recording import Recording
        from mixedvoices.core.version import Version

        recording_data = params["recording_data"]
        version_data = params["version_data"]
        user_channel = params["user_channel"]

        recording = Recording(
            recording_id=recording_data["recording_id"],
            audio_path=recording_data["audio_path"],
            version_id=recording_data["version_id"],
            project_id=recording_data["project_id"],
            is_successful=recording_data["is_successful"],
            metadata=recording_data["metadata"],
            summary=recording_data["summary"],
            combined_transcript=recording_data["combined_transcript"],
        )

        version = Version._load(
            project_id=version_data["project_id"],
            version_id=version_data["version_id"],
        )

        return {
            "recording": recording,
            "version": version,
            "user_channel": user_channel,
        }

    def _save_task(self, task: Task):
        """Save task state to appropriate folder based on status."""
        file_name = f"{task.task_id}.json"
        for folder in self.folder_paths.values():
            old_path = os.path.join(folder, file_name)
            if os.path.exists(old_path):
                os.remove(old_path)

        new_path = os.path.join(self.folder_paths[task.status], file_name)
        d = task.to_dict()
        save_json(d, new_path)

    def _load_pending_tasks(self):
        """Load pending and in-progress tasks, ordered by creation time."""
        pending_tasks = []
        # Load from both pending and in-progress folders
        for status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            folder = self.folder_paths[status]
            if not os.path.exists(folder):
                continue

            for filename in os.listdir(folder):
                if not filename.endswith(".json"):
                    continue

                task = self._load_task_from_file(folder, filename)
                if task:
                    pending_tasks.append(task)

        # Sort tasks by creation time
        pending_tasks.sort(key=lambda x: x.created_at)

        # Add to queue and dictionary
        for task in pending_tasks:
            # Reset in-progress tasks to pending
            if task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.PENDING
                task.started_at = None
                self._save_task(task)

            self.tasks[task.task_id] = task
            self.task_queue.put(task.task_id)

    def _load_task_from_file(self, folder_path: str, filename: str) -> Optional[Task]:
        """Load a single task from a file."""
        task_path = os.path.join(folder_path, filename)
        try:
            task_data = load_json(task_path)
            return Task(
                task_id=task_data["task_id"],
                task_type=task_data["task_type"],
                params=task_data["params"],
                status=TaskStatus(task_data["status"]),
                created_at=task_data["created_at"],
                started_at=task_data.get("started_at"),
                completed_at=task_data.get("completed_at"),
                error=task_data.get("error"),
            )
        except Exception as e:
            logging.error(f"Error loading task {filename}: {str(e)}")
            return None

    def _start_processing_thread(self):
        """Start the processing thread if it's not already running."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_queue, name="TaskProcessingThread"
            )
            self.processing_thread.start()

    def _process_queue(self):
        main_thread = threading.main_thread()

        while not (
            not main_thread.is_alive()
            and self.task_queue.empty()
            and not self.is_processing
        ):
            try:
                try:
                    task_id = self.task_queue.get(timeout=1.0)
                    self.is_processing = True
                except Empty:
                    self.is_processing = False
                    continue

                task = self.tasks.get(task_id)
                if task is None:
                    self.task_queue.task_done()
                    self.is_processing = False
                    continue

                try:
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = time.time()
                    self._save_task(task)

                    if task.task_type == "process_recording":
                        from mixedvoices.core import utils

                        deserialized_params = self._deserialize_task_params(
                            task.task_type, task.params
                        )
                        utils.process_recording(**deserialized_params)
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = time.time()
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    logging.error(f"Task {task_id} failed: {str(e)}")
                finally:
                    self._save_task(task)
                    self.task_queue.task_done()
                    self.is_processing = False

            except Exception:
                if "task_id" in locals():
                    self.task_queue.task_done()
                self.is_processing = False

    def add_task(self, task_type: str, **params) -> str:
        """Add a new task to the queue."""
        task_id = uuid4().hex
        serialized_params = self._serialize_task_params(task_type, params)

        task = Task(
            task_id=task_id,
            task_type=task_type,
            params=serialized_params,
            status=TaskStatus.PENDING,
            created_at=time.time(),
        )

        self.tasks[task_id] = task
        self._save_task(task)
        self.task_queue.put(task_id)
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_pending_task_count(self) -> int:
        """Get the number of pending and in-progress tasks."""
        return self.task_queue.unfinished_tasks


TASK_MANAGER = TaskManager()
