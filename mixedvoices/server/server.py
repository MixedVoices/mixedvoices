import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mixedvoices
from mixedvoices import constants
from mixedvoices.server.utils import process_vapi_webhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
    prompt: str
    success_criteria: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RecordingUpload(BaseModel):
    url: Optional[str] = None
    is_successful: Optional[bool] = None
    user_channel: Optional[str] = None


# API Routes
@app.get("/api/projects")
async def list_projects():
    """List all available projects"""
    try:
        if not os.path.exists(constants.ALL_PROJECTS_FOLDER):
            return {"projects": []}
        projects = os.listdir(constants.ALL_PROJECTS_FOLDER)
        if "_tasks" in projects:
            projects.remove("_tasks")
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects")
async def create_project(name: str):
    """Create a new project"""
    try:
        mixedvoices.create_project(name)
        logger.info(f"Project '{name}' created successfully")
        return {"message": f"Project {name} created successfully"}
    except ValueError as e:
        logger.error(f"Invalid project name '{name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating project '{name}': {str(e)}", exc_info=True)
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
                    "prompt": version.prompt,
                    "metadata": version.metadata,
                    "success_criteria": version.success_criteria,
                    "recording_count": len(version.recordings),
                }
            )
        return {"versions": versions_data}
    except ValueError as e:
        logger.error(f"Project '{project_name}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error listing versions for project '{project_name}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_name}/versions")
async def create_version(project_name: str, version_data: VersionCreate):
    """Create a new version in a project"""
    try:
        project = mixedvoices.load_project(project_name)
        project.create_version(
            version_data.name,
            prompt=version_data.prompt,
            success_criteria=version_data.success_criteria,
            metadata=version_data.metadata,
        )
        logger.info(
            f"Version '{version_data.name}' created successfully in project '{project_name}'"
        )
        return {"message": f"Version {version_data.name} created successfully"}
    except ValueError as e:
        logger.error(
            f"Error creating version '{version_data.name}' in project '{project_name}': {str(e)}"
        )
        raise HTTPException(
            status_code=400, detail=f"Version {version_data.name} already exists"
        ) from e
    except Exception as e:
        logger.error(
            f"Error creating version '{version_data.name}' in project '{project_name}': {str(e)}",
            exc_info=True,
        )
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
                "number_of_failed_calls": step.number_of_failed_calls,
                "previous_step_id": step.previous_step_id,
                "next_step_ids": step.next_step_ids,
            }
            for step_id, step in version.steps.items()
        ]
        return {"steps": steps_data}
    except ValueError as e:
        logger.error(
            f"Version '{version_name}' not found in project '{project_name}': {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting flow data for version '{version_name}' in project '{project_name}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/projects/{project_name}/versions/{version_name}/recordings/{recording_id}/flow"
)
async def get_recording_flow(project_name: str, version_name: str, recording_id: str):
    """Get the flow chart data for a recording"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        recording = version.recordings.get(recording_id, None)
        if recording is None:
            raise ValueError(f"Recording {recording_id} not found in version {version_name}")

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
        logger.error(
            f"Recording '{recording_id}' not found in version '{version_name}' of project '{project_name}': {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting flow data for recording '{recording_id}' in version '{version_name}' of project '{project_name}': {str(e)}",
            exc_info=True,
        )
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
                "success_explanation": recording.success_explanation,
                "metadata": recording.metadata,
                "task_status": recording.task_status,
                "llm_metrics": recording.llm_metrics,
                "call_metrics": recording.call_metrics,
            }
            for recording_id, recording in version.recordings.items()
        ]
        return {"recordings": recordings_data}
    except ValueError as e:
        logger.error(
            f"Version '{version_name}' or project '{project_name}' does not exist: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error listing recordings for version '{version_name}' in project '{project_name}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_name}/versions/{version_name}/recordings")
async def add_recording(
    project_name: str,
    version_name: str,
    is_successful: Optional[bool] = None,
    user_channel: Optional[str] = None,
    file: Optional[UploadFile] = None,
    recording_data: Optional[RecordingUpload] = None,
):
    """Add a new recording to a version"""
    logger.info(
        f"Adding recording to version '{version_name}' in project '{project_name}'"
    )
    logger.debug(f"is_successful: {is_successful}")
    logger.debug(f"recording_data: {recording_data}")

    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)

        if file:
            temp_path = Path(f"/tmp/{file.filename}")
            try:
                with temp_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                recording = version.add_recording(
                    str(temp_path),
                    blocking=False,
                    is_successful=is_successful,
                    user_channel=user_channel,
                )
                logger.info(f"Recording is being processed: {recording.recording_id}")
                return {
                    "message": "Recording is being processed",
                    "recording_id": recording.recording_id,
                }
            finally:
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug(f"Temporary file removed: {temp_path}")

        elif recording_data and recording_data.url:
            # TODO: Implement URL upload and processing
            logger.error("URL upload not implemented yet")
            raise HTTPException(
                status_code=501, detail="URL upload not implemented yet"
            )
        else:
            logger.error("No file or URL provided")
            raise HTTPException(status_code=400, detail="No file or URL provided")

    except ValueError as e:
        logger.error(f"Invalid recording data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error adding recording: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/projects/{project_name}/versions/{version_name}/steps/{step_id}/recordings"
)
async def list_step_recordings(project_name: str, version_name: str, step_id: str):
    """Get all recordings that reached a specific step"""
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        step = version.steps.get(step_id, None)
        if step is None:
            raise ValueError(f"Step {step_id} not found in version {version_name}")

        recordings_data = []
        for recording_id in step.recording_ids:
            recording = version.recordings[recording_id]
            recordings_data.append(
                {
                    "id": recording.recording_id,
                    "audio_path": recording.audio_path,
                    "created_at": recording.created_at,
                    "combined_transcript": recording.combined_transcript,
                    "step_ids": recording.step_ids,
                    "summary": recording.summary,
                    "duration": recording.duration,
                    "is_successful": recording.is_successful,
                    "success_explanation": recording.success_explanation,
                    "metadata": recording.metadata,
                    "task_status": recording.task_status,
                    "llm_metrics": recording.llm_metrics,
                    "call_metrics": recording.call_metrics,
                }
            )

        return {"recordings": recordings_data}
    except ValueError as e:
        logger.error(
            f"Step '{step_id}' or version '{version_name}' or project '{project_name}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting recordings for step '{step_id}' in version '{version_name}' of project '{project_name}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/{project_name}/{version_name}/{provider_name}")
async def handle_webhook(
    project_name: str, version_name: str, provider_name: str, request: Request
):
    """Handle incoming webhook, download the recording, and add it to the version"""
    logger.info(
        f"Received webhook for provider '{provider_name}' - project: '{project_name}', version: '{version_name}'"
    )

    try:
        webhook_data = await request.json()
        logger.debug(f"Webhook data received: {webhook_data}")

        if provider_name == "vapi":
            data = process_vapi_webhook(webhook_data)
            stereo_url = data["call_info"]["stereo_recording_url"]
            is_successful = data.pop("is_successful", None)
            summary = data.pop("summary", None)
            transcript = data.pop("transcript", None)
            call_id = data["id_info"]["call_id"]
        else:
            logger.error(f"Invalid provider name: {provider_name}")
            raise HTTPException(status_code=400, detail="Invalid provider name")

        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)

        temp_path = Path(f"/tmp/{call_id}.wav")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(stereo_url) as response:
                    if response.status == 200:
                        with open(temp_path, "wb") as f:
                            f.write(await response.read())
                            logger.info(
                                f"Audio file downloaded successfully: {call_id}.wav"
                            )
                    else:
                        logger.error(
                            f"Failed to download audio file: {response.status}"
                        )
                        raise HTTPException(
                            status_code=response.status,
                            detail="Failed to download audio file",
                        )

            recording = version.add_recording(
                str(temp_path),
                blocking=True,
                is_successful=is_successful,
                metadata=data,
                summary=summary,
                transcript=transcript
            )
            logger.info(f"Recording processed successfully: {recording.recording_id}")

            return {
                "message": "Webhook processed and recording added successfully",
                "recording_id": recording.recording_id,
            }

        finally:
            if temp_path.exists():
                temp_path.unlink()
                logger.debug(f"Temporary file removed: {temp_path}")

    except ValueError as e:
        logger.error(f"Invalid webhook data: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_name}/versions/{version_name}/evals")
async def list_evals(project_name: str, version_name: str):
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        evals = version.evals
        eval_data = []
        for eval_id, cur_eval in evals.items():
            eval_data.append(
                {
                    "eval_id": eval_id,
                    "created_at": cur_eval.created_at,
                }
            )
        return {"evals": eval_data}
    except ValueError as e:
        logger.error(
            f"Version '{version_name}' or project '{project_name}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error listing evals: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_name}/versions/{version_name}/evals/{eval_id}")
async def get_eval_details(project_name: str, version_name: str, eval_id: str):
    try:
        project = mixedvoices.load_project(project_name)
        version = project.load_version(version_name)
        current_eval = version.evals.get(eval_id, None)
        if current_eval is None:
            raise ValueError(f"Eval {eval_id} not found in version {version_name}")
        agents = current_eval.eval_agents
        agent_data = []
        for agent in agents:
            agent_data.append(
                {
                    "prompt": agent.eval_prompt,
                    "started": agent.started,
                    "ended": agent.ended,
                    "transcript": agent.transcript,
                    "scores": agent.scores,
                    "error": agent.error,
                }
            )

        return {"agents": agent_data}
    except ValueError as e:
        logger.error(
            f"Eval '{eval_id}' or version '{version_name}' or project '{project_name}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting eval details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


def run_server(port: int = 7760):
    """Run the FastAPI server"""
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
