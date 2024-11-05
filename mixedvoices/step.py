from itertools import count
from uuid import uuid4
from mixedvoices.constants import ALL_PROJECTS_FOLDER
from mixedvoices.recording import Recording
from typing import Optional
import json
import os

class Step:
    def __init__(self, name, version_id, project_id, recording_ids: Optional[list] = None, number_of_successful_calls: int = 0, previous_step_id: Optional[str] = None, next_step_ids: Optional[list] = None, step_id: Optional[str] = None):
        self.step_id = step_id or str(uuid4())
        self.name = name
        self.version_id = version_id
        self.project_id = project_id
        self.recording_ids = recording_ids or []
        self.number_of_successful_calls = number_of_successful_calls  # out of the terminated calls
        self.previous_step_id = previous_step_id
        self.next_step_ids = next_step_ids or []
        self.previous_step = None
        self.next_steps = []
        
    @property
    def number_of_calls(self):
        return len(self.recording_ids)

    @property
    def number_of_terminated_calls(self):
        return count(not next_step for next_step in self.next_steps)
    
    @property
    def path(self):
        return os.path.join(ALL_PROJECTS_FOLDER, self.project_id, self.version_id, "steps", self.step_id, "info.json")

    def record_usage(self, recording: Recording, is_final_step, is_successful):
        self.recording_ids.append(recording.recording_id)
        if is_final_step and is_successful:
            self.number_of_successful_calls += 1

    def save(self):
        with open(self.path, 'w') as f:
            d = {
                'name': self.name,
                'recording_ids': self.recording_ids,
                'number_of_successful_calls': self.number_of_successful_calls,
                'previous_step_id': self.previous_step_id,
                'next_step_ids': self.next_step_ids
            }
            f.write(json.dumps(d))
    
    @classmethod
    def load(cls, project_id, version_id, step_id):
        path = os.path.join(ALL_PROJECTS_FOLDER, project_id, version_id, "steps", step_id, "info.json")
        with open(path, 'r') as f:
            d = json.loads(f.read())

        d.update({"project_id": project_id, "version_id": version_id, "step_id": step_id})
        return cls(**d)    
       




