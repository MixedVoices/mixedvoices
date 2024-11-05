import os
from typing import Dict, Any, Optional
from mixedvoices.constants import ALL_PROJECTS_FOLDER
from mixedvoices.version import Version

class Project:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_folder = f"{ALL_PROJECTS_FOLDER}/{project_id}"

    @property
    def versions(self):
        return os.listdir(self.project_folder)

    def create_version(self, version_id: str, metadata: Optional[Dict[str, Any]] = None):
        if version_id in self.versions:
            raise ValueError(f"Version {version_id} already exists")
        os.makedirs(f"{self.project_folder}/{version_id}")
        version = Version(version_id, self.project_id, metadata)
        return version
    
    def load_version(self, version_id: str):
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} does not exist")
        return Version.load(self.project_id, version_id)
        
