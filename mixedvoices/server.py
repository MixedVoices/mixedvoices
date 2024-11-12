import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mixedvoices
import mixedvoices.constants

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Models
class VersionCreate(BaseModel):
    name: str
    metadata: Dict[str, Any]


class RecordingUpload(BaseModel):
    url: Optional[str] = None
    is_successful: Optional[bool] = None


# API Routes
@app.get("/api/projects")
async def list_projects():
    """List all available projects"""
    try:
        if not os.path.exists(mixedvoices.constants.ALL_PROJECTS_FOLDER):
            return {"projects": []}
        projects = os.listdir(mixedvoices.constants.ALL_PROJECTS_FOLDER)
        if "_tasks" in projects:
            projects.remove("_tasks")
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects")
async def create_project(name: str):
    """Create a new project"""
    try:
        mixedvoices.create_project(name)
        return {"message": f"Project {name} created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_name}/versions")
async def list_versions(project_name: str):
    """List all versions for a project"""
    try:
        project = mixedvoices.load_project(project_name)
        versions_data = []
        for version_id in project.versions:
            version = project.load_version(version_id)
            versions_data.append(
                {
                    "name": version_id,
                    "metadata": version.metadata,
                    "recording_count": len(version.recordings),
                }
            )
        return {"versions": versions_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_name}/versions")
async def create_version(project_name: str, version_data: VersionCreate):
    """Create a new version in a project"""
    try:
        project = mixedvoices.load_project(project_name)
        project.create_version(version_data.name, metadata=version_data.metadata)
        return {"message": f"Version {version_data.name} created successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Version {version_data.name} already exists"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_name}/versions/{version_name}/flow")
async def get_version_flow(project_name: str, version_name: str):
    """Get the flow chart data for a version"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)

        steps_data = [
            {
                "id": step_id,
                "name": step.name,
                "number_of_calls": step.number_of_calls,
                "number_of_terminated_calls": step.number_of_terminated_calls,
                "number_of_successful_calls": step.number_of_successful_calls,
                "previous_step_id": step.previous_step_id,
                "next_step_ids": step.next_step_ids,
            }
            for step_id, step in version.steps.items()
        ]
        return {"steps": steps_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/projects/{project_name}/versions/{version_name}/recordings/{recording_id}/flow"
)
async def get_recording_flow(project_name: str, version_name: str, recording_id: str):
    """Get the flow chart data for a recording"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        recording = version.recordings[recording_id]

        steps_data = []
        for step_id in recording.step_ids:
            step = version.steps[step_id]
            steps_data.append(
                {
                    "id": step.step_id,
                    "name": step.name,
                }
            )
        return {"steps": steps_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_name}/versions/{version_name}/recordings")
async def list_recordings(project_name: str, version_name: str):
    """List all recordings in a version"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        recordings_data = [
            {
                "id": recording_id,
                "audio_path": recording.audio_path,
                "created_at": recording.created_at,
                "combined_transcript": recording.combined_transcript,
                "step_ids": recording.step_ids,
                "summary": recording.summary,
                "duration": recording.duration,
                "is_successful": recording.is_successful,
            }
            for recording_id, recording in version.recordings.items()
        ]
        return {"recordings": recordings_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_name}/versions/{version_name}/recordings")
async def add_recording(
    project_name: str,
    version_name: str,
    is_successful: Optional[bool] = None,
    file: Optional[UploadFile] = None,
    recording_data: Optional[RecordingUpload] = None,
):
    """Add a new recording to a version"""
    print(is_successful)
    print(recording_data)
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)

        if file:
            # Save uploaded file to temporary location
            temp_path = Path(f"/tmp/{file.filename}")
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process the recording
            recording = version.add_recording(
                str(temp_path), blocking=True, is_successful=is_successful
            )

            # Clean up
            temp_path.unlink()

            return {
                "message": "Recording added successfully",
                "recording_id": recording.recording_id,
            }
        elif recording_data and recording_data.url:
            # TODO: Implement URL upload and processing
            raise HTTPException(
                status_code=501, detail="URL upload not implemented yet"
            )
        else:
            raise HTTPException(status_code=400, detail="No file or URL provided")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/projects/{project_name}/versions/{version_name}/steps/{step_id}/recordings"
)
async def get_step_recordings(project_name: str, version_name: str, step_id: str):
    """Get all recordings that reached a specific step"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        step = version.steps[step_id]

        recordings_data = []
        for recording_id in step.recording_ids:
            recording = version.recordings[recording_id]
            recordings_data.append(
                {
                    "id": recording.recording_id,
                    "created_at": recording.created_at,
                    "combined_transcript": recording.combined_transcript,
                    "step_ids": recording.step_ids,
                    "summary": recording.summary,
                    "duration": recording.duration,
                    "is_successful": recording.is_successful,
                }
            )

        return {"recordings": recordings_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def run_server(port: int = 8000):
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=port)
