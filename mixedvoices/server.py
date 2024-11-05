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
import typer
import webbrowser
import pkg_resources
import json


app = FastAPI()
cli = typer.Typer()

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


# HTML template with embedded JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MixedVoices</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/javascript">
        const e = React.createElement;
        
        const App = () => {
            const [projects, setProjects] = React.useState([]);
            const [selectedProject, setSelectedProject] = React.useState(null);
            const [versions, setVersions] = React.useState([]);
            const [error, setError] = React.useState(null);
            const [loading, setLoading] = React.useState(false);
            const [view, setView] = React.useState('projects');
            const [flowData, setFlowData] = React.useState(null);
            const [newProjectName, setNewProjectName] = React.useState('');
            const [newVersionData, setNewVersionData] = React.useState({ name: '', metadata: {} });
            
            const fetchProjects = async () => {
                try {
                    const response = await fetch('/api/projects');
                    const data = await response.json();
                    setProjects(data.projects);
                } catch (err) {
                    setError(err.message);
                }
            };

            const fetchVersions = async (projectName) => {
                try {
                    const response = await fetch(`/api/projects/${projectName}/versions`);
                    const data = await response.json();
                    setVersions(data.versions);
                } catch (err) {
                    setError(err.message);
                }
            };

            const createProject = async () => {
                try {
                    await fetch(`/api/projects?name=${encodeURIComponent(newProjectName)}`, {
                        method: 'POST'
                    });
                    fetchProjects();
                    setNewProjectName('');
                } catch (err) {
                    setError(err.message);
                }
            };

            React.useEffect(() => {
                fetchProjects();
            }, []);

            const Card = ({ children, onClick, className = '' }) => {
                return e('div', {
                    className: `p-4 border rounded-lg shadow-sm hover:shadow-md cursor-pointer ${className}`,
                    onClick
                }, children);
            };

            const ProjectsList = () => {
                return e('div', { className: 'grid grid-cols-1 md:grid-cols-3 gap-4 p-4' },
                    [
                        ...projects.map(project => 
                            e(Card, {
                                key: project,
                                onClick: () => {
                                    setSelectedProject(project);
                                    fetchVersions(project);
                                    setView('versions');
                                }
                            }, e('h3', { className: 'text-lg font-medium' }, project))
                        ),
                        e(Card, {
                            key: 'new',
                            className: 'border-dashed',
                            onClick: () => {
                                const name = prompt('Enter project name:');
                                if (name) {
                                    setNewProjectName(name);
                                    createProject();
                                }
                            }
                        }, e('div', { className: 'text-center text-gray-500' }, '+ New Project'))
                    ]
                );
            };

            const VersionsList = () => {
                return e('div', { className: 'p-4' }, [
                    e('div', { className: 'mb-4 flex items-center' }, [
                        e('button', {
                            className: 'text-blue-500 hover:text-blue-700',
                            onClick: () => setView('projects')
                        }, '← Back'),
                        e('h2', { className: 'ml-4 text-2xl font-bold' }, selectedProject)
                    ]),
                    e('div', { className: 'grid grid-cols-1 md:grid-cols-3 gap-4' },
                        [
                            ...versions.map(version =>
                                e(Card, {
                                    key: version.name,
                                    onClick: () => {
                                        setView('version-detail');
                                    }
                                }, [
                                    e('h3', { className: 'text-lg font-medium' }, version.name),
                                    e('p', { className: 'text-sm text-gray-500' },
                                        `${version.recording_count} recordings`
                                    )
                                ])
                            ),
                            e(Card, {
                                key: 'new',
                                className: 'border-dashed',
                                onClick: () => {
                                    const name = prompt('Enter version name:');
                                    if (name) {
                                        setNewVersionData({ name, metadata: {} });
                                        // Handle version creation
                                    }
                                }
                            }, e('div', { className: 'text-center text-gray-500' }, '+ New Version'))
                        ]
                    )
                ]);
            };

            return e('div', { className: 'min-h-screen bg-gray-50' },
                e('div', { className: 'max-w-7xl mx-auto py-6' },
                    view === 'projects' ? e(ProjectsList) :
                    view === 'versions' ? e(VersionsList) :
                    null
                )
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(e(App));
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_app():
    return HTML_TEMPLATE

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

@cli.command()
def run(port: int = typer.Option(8000, help="Port to run the server on")):
    """Run the MixedVoices web interface"""
    print(f"Starting MixedVoices server on http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    run_server(port)

if __name__ == "__main__":
    cli()