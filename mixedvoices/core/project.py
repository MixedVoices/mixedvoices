import os
from typing import Any, Dict, Optional

import mixedvoices.constants as constants
from mixedvoices.core.version import Version
from mixedvoices.utils import validate_name


class Project:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_folder = os.path.join(constants.ALL_PROJECTS_FOLDER, project_id)

    @property
    def versions(self):
        all_files = os.listdir(self.project_folder)
        return [
            f for f in all_files if os.path.isdir(os.path.join(self.project_folder, f))
        ]

    def create_version(
        self,
        version_id: str,
        prompt: str,
        success_criteria: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new version in the project

        Args:
            version_id (str): Name of the version
            prompt (str): Prompt used by the voice agent
            success_criteria (Optional[str]): Success criteria for the version. Used to automatically determine if a recording is successful or not. Defaults to None.
            metadata (Optional[Dict[str, Any]]): Metadata to be associated with the version. Defaults to None.
        """  # noqa E501
        validate_name(version_id, "version_id")
        if version_id in self.versions:
            raise ValueError(f"Version {version_id} already exists")
        version_path = os.path.join(self.project_folder, version_id)
        os.makedirs(version_path)
        os.makedirs(os.path.join(version_path, "recordings"))
        os.makedirs(os.path.join(version_path, "steps"))
        version = Version(
            version_id, self.project_id, prompt, success_criteria, metadata
        )
        version.save()
        return version

    def load_version(self, version_id: str):
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} does not exist")
        return Version.load(self.project_id, version_id)
