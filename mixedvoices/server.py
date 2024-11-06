from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from pathlib import Path
import os
import shutil
from mixedvoices.constants import ALL_PROJECTS_FOLDER
import mixedvoices

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

# API Routes
@app.get("/api/projects")
async def list_projects():
    """List all available projects"""
    try:
        if not os.path.exists(ALL_PROJECTS_FOLDER):
            return {"projects": []}
        projects = os.listdir(ALL_PROJECTS_FOLDER)
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(name: str):
    """Create a new project"""
    try:
        project = mixedvoices.create_project(name)
        return {"message": f"Project {name} created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/versions")
async def list_versions(project_name: str):
    """List all versions for a project"""
    try:
        project = mixedvoices.load_project(project_name)
        versions_data = []
        for version_id in project.versions:
            version = project.load_version(version_id)
            versions_data.append({
                "name": version_id,
                "metadata": version.metadata,
                "recording_count": len(version.recordings)
            })
        return {"versions": versions_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_name}/versions")
async def create_version(project_name: str, version_data: VersionCreate):
    """Create a new version in a project"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.create_version(version_data.name, metadata=version_data.metadata)
        return {"message": f"Version {version_data.name} created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/versions/{version_name}/flow")
async def get_version_flow(project_name: str, version_name: str):
    """Get the flow chart data for a version"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        
        steps_data = []
        for step_id, step in version.steps.items():
            steps_data.append({
                "id": step.step_id,
                "name": step.name,
                "number_of_calls": step.number_of_calls,
                "number_of_terminated_calls": step.number_of_terminated_calls,
                "number_of_successful_calls": step.number_of_successful_calls,
                "previous_step_id": step.previous_step_id,
                "next_step_ids": step.next_step_ids
            })
        
        return {"steps": steps_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/projects/{project_name}/versions/{version_name}/recordings/{recording_id}/flow")
async def get_recording_flow(project_name: str, version_name: str, recording_id: str):
    """Get the flow chart data for a recording"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        recording = version.recordings[recording_id]
        
        steps_data = []
        for step_id in recording.step_ids:
            step = version.steps[step_id]
            steps_data.append({
                "id": step.step_id,
                "name": step.name,
            })
        return {"steps": steps_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/versions/{version_name}/recordings")
async def list_recordings(project_name: str, version_name: str):
    """List all recordings in a version"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        recordings_data = []
        for recording_id, recording in version.recordings.items():
            recordings_data.append({
                "id": recording.recording_id,
                "created_at": recording.created_at,
                "combined_transcript": recording.combined_transcript,
                "step_ids": recording.step_ids,
                "summary": recording.summary,
                "is_successful": recording.is_successful
            })
        return {"recordings": recordings_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_name}/versions/{version_name}/recordings")
async def add_recording(
    project_name: str, 
    version_name: str, 
    file: Optional[UploadFile] = None,
    recording_data: Optional[RecordingUpload] = None
):
    """Add a new recording to a version"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        
        if file:
            # Save uploaded file to temporary location
            temp_path = Path(f"/tmp/{file.filename}")
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Process the recording
            recording = version.add_recording(str(temp_path))
            
            # Clean up
            temp_path.unlink()
            
            return {
                "message": "Recording added successfully",
                "recording_id": recording.recording_id
            }
        elif recording_data and recording_data.url:
            # TODO: Implement URL download and processing
            raise HTTPException(status_code=501, detail="URL upload not implemented yet")
        else:
            raise HTTPException(status_code=400, detail="No file or URL provided")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_name}/versions/{version_name}/steps/{step_id}/recordings")
async def get_step_recordings(project_name: str, version_name: str, step_id: str):
    """Get all recordings that reached a specific step"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        step = version.steps[step_id]
        
        recordings_data = []
        for recording_id in step.recording_ids:
            recording = version.recordings[recording_id]
            recordings_data.append({
                "id": recording.recording_id,
                "created_at": recording.created_at,
                "combined_transcript": recording.combined_transcript,
                "step_ids": recording.step_ids,
                "summary": recording.summary,
                "is_successful": recording.is_successful
            })
        
        return {"recordings": recordings_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_server(port: int = 8000):
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=port)