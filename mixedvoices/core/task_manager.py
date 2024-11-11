import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from typing import Any, Dict, Optional

import mixedvoices.constants as constants


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
        self.tasks_folder = os.path.join(constants.ALL_PROJECTS_FOLDER, "_tasks")
        os.makedirs(self.tasks_folder, exist_ok=True)
        self._load_pending_tasks()
        self._start_processing_thread()

    def _serialize_task_params(
        self, task_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert task parameters into JSON-serializable format."""
        if task_type == "process_recording":
            recording = params["recording"]
            version = params["version"]
            return {
                "recording_data": {
                    "recording_id": recording.recording_id,
                    "audio_path": recording.audio_path,
                    "version_id": recording.version_id,
                    "project_id": recording.project_id,
                },
                "version_data": {
                    "version_id": version.version_id,
                    "project_id": version.project_id,
                },
            }
        return params

    def _deserialize_task_params(
        self, task_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert serialized parameters back into required objects."""
        if task_type == "process_recording":
            from mixedvoices.core.recording import Recording
            from mixedvoices.core.version import Version

            recording_data = params["recording_data"]
            version_data = params["version_data"]

            recording = Recording(
                recording_id=recording_data["recording_id"],
                audio_path=recording_data["audio_path"],
                version_id=recording_data["version_id"],
                project_id=recording_data["project_id"],
            )

            version = Version.load(
                project_id=version_data["project_id"],
                version_id=version_data["version_id"],
            )

            return {"recording": recording, "version": version}
        return params

    def _save_task(self, task: Task):
        """Save task state to disk."""
        task_path = os.path.join(self.tasks_folder, f"{task.task_id}.json")
        with open(task_path, "w") as f:
            json.dump(task.to_dict(), f)

    def _load_pending_tasks(self):
        """Load any pending tasks from disk that weren't completed in previous runs."""
        if not os.path.exists(self.tasks_folder):
            return

        for task_file in os.listdir(self.tasks_folder):
            if not task_file.endswith(".json"):
                continue

            task_path = os.path.join(self.tasks_folder, task_file)
            try:
                with open(task_path, "r") as f:
                    task_data = json.load(f)
                    task = Task(
                        task_id=task_data["task_id"],
                        task_type=task_data["task_type"],
                        params=task_data["params"],
                        status=TaskStatus(task_data["status"]),
                        created_at=task_data["created_at"],
                        started_at=task_data.get("started_at"),
                        completed_at=task_data.get("completed_at"),
                        error=task_data.get("error"),
                    )

                    if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                        self.tasks[task.task_id] = task
                        self.task_queue.put(task.task_id)
            except Exception as e:
                logging.error(f"Error loading task {task_file}: {str(e)}")

    def _start_processing_thread(self):
        """Start the processing thread if it's not already running."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_queue, name="TaskProcessingThread"
            )
            self.processing_thread.start()

    def _process_queue(self):
        main_thread = threading.main_thread()

        while True:
            if not main_thread.is_alive() and self.task_queue.empty():
                break

            try:
                try:
                    task_id = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue

                task = self.tasks.get(task_id)
                if task is None:
                    self.task_queue.task_done()
                    continue

                try:
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = time.time()
                    self._save_task(task)

                    if task.task_type == "process_recording":
                        from mixedvoices.utils import process_recording

                        deserialized_params = self._deserialize_task_params(
                            task.task_type, task.params
                        )
                        process_recording(**deserialized_params)
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = time.time()
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    logging.error(f"Task {task_id} failed: {str(e)}")
                finally:
                    self._save_task(task)
                    self.task_queue.task_done()

            except Exception:
                if "task_id" in locals():
                    self.task_queue.task_done()

    def add_task(self, task_type: str, **params) -> str:
        """Add a new task to the queue."""
        import uuid

        task_id = str(uuid.uuid4())
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

    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get the current status of a task."""
        return self.tasks.get(task_id)

    def get_pending_task_count(self) -> int:
        """Get the number of pending and in-progress tasks."""
        return self.task_queue.unfinished_tasks

    def wait_for_task(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional[Task]:
        start_time = time.time()
        while True:
            task = self.get_task_status(task_id)
            if task is None:
                return None

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return task

            if timeout is not None and time.time() - start_time > timeout:
                return task

            time.sleep(0.1)

    def wait_for_all_tasks(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all current tasks to complete.

        Args:
            timeout: Maximum time to wait (in seconds). If None, wait indefinitely.

        Returns:
            bool: True if all tasks completed, False if timed out
        """
        try:
            if timeout is not None:
                start = time.time()
                while self.task_queue.unfinished_tasks > 0:
                    if time.time() - start > timeout:
                        return False
                    time.sleep(0.1)
            else:
                self.task_queue.join()
            return True
        except Exception:
            return False
