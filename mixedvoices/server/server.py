import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mixedvoices
from mixedvoices import TestCaseGenerator
from mixedvoices.metrics.metric import Metric
from mixedvoices.server.utils import copy_file_content, process_vapi_webhook

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
    metadata: Optional[Dict[str, Any]] = None


class ProjectCreate(BaseModel):
    metrics: List[Dict]


class MetricCreate(BaseModel):
    name: str
    definition: str
    scoring: str
    include_prompt: bool


class MetricUpdate(BaseModel):
    definition: str
    scoring: str
    include_prompt: bool


class EvalCreate(BaseModel):
    test_cases: List[str]
    metric_names: List[str]


class SuccessCriteria(BaseModel):
    success_criteria: str


# API Routes
@app.get("/api/projects")
async def list_projects():
    """List all available projects"""
    try:
        return {"projects": mixedvoices.list_projects()}
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects")
async def create_project(
    name: str, success_criteria: Optional[str], metrics_data: ProjectCreate
):
    # here the dict will have name, definition and scoring (which can be binary(PASS/FAIL) or continuous (0-10))
    """Create a new project"""
    try:
        metrics = [Metric(**metric) for metric in metrics_data.metrics]
        mixedvoices.create_project(name, metrics, success_criteria)
        return {"message": f"Project {name} created successfully", "project_id": name}
    except ValueError as e:
        logger.error(f"Invalid project name '{name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileExistsError as e:
        logger.error(f"Project '{name}' already exists: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating project '{name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/versions")
async def list_versions(project_id: str):
    """List all versions for a project"""
    try:
        project = mixedvoices.load_project(project_id)
        versions_data = []
        for version_id in project.version_ids:
            version = project.load_version(version_id)
            versions_data.append(version.info)
        return {"versions": versions_data}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error listing versions for project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/versions/{version_id}")
async def get_version(project_id: str, version_id: str):
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
        return version.info
    except KeyError as e:
        logger.error(
            f"Project '{project_id}' or version '{version_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting version '{version_id}' for project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/default_metrics")
async def list_default_metrics():
    try:
        metrics = mixedvoices.metrics.get_all_default_metrics()
        metrics = [metric.to_dict() for metric in metrics]
        return {"metrics": metrics}
    except Exception as e:
        logger.error(f"Error listing default metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/metrics")
async def list_metrics(project_id: str):
    """List all metrics for a project"""
    try:
        project = mixedvoices.load_project(project_id)
        return {"metrics": [metric.to_dict() for metric in project.metrics]}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error listing metrics for project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/metrics")
async def add_metric(project_id: str, metric_data: MetricCreate):
    try:
        project = mixedvoices.load_project(project_id)
        metric = Metric(
            name=metric_data.name,
            definition=metric_data.definition,
            scoring=metric_data.scoring,
            include_prompt=metric_data.include_prompt,
        )
        project.add_metrics([metric])
        return {"message": f"Metric {metric.name} created successfully"}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileExistsError as e:
        logger.error(
            f"Metric with name '{metric_data.name}' already exists in project '{project_id}': {str(e)}"
        )
        raise HTTPException(
            status_code=409, detail=f"Metric {metric_data.name} already exists"
        )
    except Exception as e:
        logger.error(f"Error creating metric: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/metrics/{metric_name}")
async def update_metric(project_id: str, metric_name: str, metric_data: MetricUpdate):
    try:
        project = mixedvoices.load_project(project_id)
        metric = Metric(
            name=metric_name,
            definition=metric_data.definition,
            scoring=metric_data.scoring,
            include_prompt=metric_data.include_prompt,
        )
        project.update_metric(metric)
        return {"message": f"Metric {metric_name} updated successfully"}
    except KeyError as e:
        logger.error(
            f"Project '{project_id}' or metric '{metric_name}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error updating metric: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/versions")
async def create_version(project_id: str, version_data: VersionCreate):
    """Create a new version in a project"""
    try:
        project = mixedvoices.load_project(project_id)
        project.create_version(
            version_data.name,
            prompt=version_data.prompt,
            metadata=version_data.metadata,
        )
        return {"message": f"Version {version_data.name} created successfully"}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileExistsError as e:
        logger.error(
            f"Version '{version_data.name}' already exists in project '{project_id}': {str(e)}"
        )
        raise HTTPException(
            status_code=409, detail=f"Version {version_data.name} already exists"
        ) from e
    except ValueError as e:
        logger.error(
            f"Invalid version name '{version_data.name}' in project '{project_id}': {str(e)}"
        )
        raise HTTPException(
            status_code=400, detail=f"Invalid version name {version_data.name}"
        ) from e
    except Exception as e:
        logger.error(
            f"Error creating version '{version_data.name}' in project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/success_criteria")
async def get_success_criteria(project_id: str):
    """Get the success criteria for a version"""
    try:
        project = mixedvoices.load_project(project_id)
        return {"success_criteria": project.success_criteria}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting success criteria for project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/success_criteria")
async def update_success_criteria(project_id: str, success_criteria: SuccessCriteria):
    """Update the success criteria for a version"""
    try:
        project = mixedvoices.load_project(project_id)
        project.update_success_criteria(success_criteria.success_criteria)
        return {"message": "Success criteria updated successfully"}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error updating success criteria for project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/versions/{version_id}/flow")
async def get_version_flow(project_id: str, version_id: str):
    """Get the flow chart data for a version"""
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
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
            for step_id, step in version._steps.items()
        ]
        return {"steps": steps_data}
    except KeyError as e:
        logger.error(
            f"Version '{version_id}' or project '{project_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting flow data for version '{version_id}' in project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/projects/{project_id}/versions/{version_id}/recordings/{recording_id}/flow"
)
async def get_recording_flow(project_id: str, version_id: str, recording_id: str):
    """Get the flow chart data for a recording"""
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
        recording = version.get_recording(recording_id)

        steps_data = []
        for step_id in recording.step_ids:
            step = version._steps[step_id]
            steps_data.append(
                {
                    "id": step.step_id,
                    "name": step.name,
                }
            )
        return {"steps": steps_data}
    except KeyError as e:
        logger.error(
            f"Recording '{recording_id}' or version '{version_id}' or project '{project_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting flow data for recording '{recording_id}' in version '{version_id}' of project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/versions/{version_id}/recordings")
async def list_recordings(project_id: str, version_id: str):
    """List all recordings in a version"""
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
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
            for recording_id, recording in version._recordings.items()
        ]
        return {"recordings": recordings_data}
    except KeyError as e:
        logger.error(
            f"Version '{version_id}' or project '{project_id}' does not exist: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error listing recordings for version '{version_id}' in project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/versions/{version_id}/recordings")
async def add_recording(
    project_id: str,
    version_id: str,
    file: UploadFile,
    user_channel: str = "left",
    is_successful: Optional[bool] = None,
):
    """Add a new recording to a version"""
    logger.debug(f"is_successful: {is_successful}")

    temp_dir = None
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
        temp_path, temp_dir = copy_file_content(file)
        version.add_recording(
            str(temp_path),
            blocking=False,
            is_successful=is_successful,
            user_channel=user_channel,
        )
        return {
            "message": "Recording is being processed",
        }
    except KeyError as e:
        logger.error(
            f"Version '{version_id}' or project '{project_id}' does not exist: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error adding recording: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_dir:
            temp_dir.cleanup()


@app.get("/api/projects/{project_id}/versions/{version_id}/steps/{step_id}/recordings")
async def list_step_recordings(project_id: str, version_id: str, step_id: str):
    """Get all recordings that reached a specific step"""
    try:
        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)
        step = version.get_step(step_id)
        recordings_data = []
        for recording_id in step.recording_ids:
            recording = version._recordings[recording_id]
            recordings_data.append(
                {
                    "id": recording.id,
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
    except KeyError as e:
        logger.error(
            f"Step '{step_id}' or version '{version_id}' or project '{project_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting recordings for step '{step_id}' in version '{version_id}' of project '{project_id}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/webhook/{project_id}/{version_id}/{provider_name}")
async def handle_webhook(
    project_id: str, version_id: str, provider_name: str, request: Request
):
    """Handle incoming webhook, download the recording, and add it to the version"""
    try:
        webhook_data = await request.json()
        logger.debug(f"Webhook data received: {webhook_data}")

        project = mixedvoices.load_project(project_id)
        version = project.load_version(version_id)

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

        temp_path = Path(f"/tmp/{call_id}.wav")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(stereo_url) as response:
                    if response.status == 200:
                        with open(temp_path, "wb") as f:
                            f.write(await response.read())
                    else:
                        logger.error(
                            f"Failed to download audio file: {response.status}"
                        )
                        raise HTTPException(
                            status_code=response.status,
                            detail="Failed to download audio file",
                        )

            version.add_recording(
                str(temp_path),
                blocking=True,
                is_successful=is_successful,
                metadata=data,
                summary=summary,
                transcript=transcript,
            )

            return {
                "message": "Webhook processed and recording added successfully",
            }

        finally:
            if temp_path.exists():
                temp_path.unlink()
                logger.debug(f"Temporary file removed: {temp_path}")

    except KeyError as e:
        logger.error(
            f"Project '{project_id}' or version '{version_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/evals")
async def list_evaluators(project_id: str):
    try:
        project = mixedvoices.load_project(project_id)
        evals = project.list_evaluators()
        eval_data = [cur_eval.info for cur_eval in evals]
        return {"evals": eval_data}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error listing evaluators: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/{project_id}/evals")
async def create_evaluator(project_id: str, eval_data: EvalCreate):
    try:
        project = mixedvoices.load_project(project_id)
        current_eval = project.create_evaluator(
            eval_data.test_cases, eval_data.metric_names
        )
        return {"eval_id": current_eval.id}
    except KeyError as e:
        logger.error(f"Project '{project_id}' not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating evaluator: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/evals/{eval_id}")
async def get_evaluator_details(project_id: str, eval_id: str):
    try:
        project = mixedvoices.load_project(project_id)
        current_eval = project.load_evaluator(eval_id)
        eval_runs = current_eval.list_eval_runs()
        eval_run_data = [eval_run.info for eval_run in eval_runs]

        return {
            "metrics": current_eval.metric_names,
            "test_cases": current_eval.test_cases,
            "eval_runs": eval_run_data,
        }
    except KeyError as e:
        logger.error(
            f"Evaluator '{eval_id}' or project '{project_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting evaluator details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/evals/{eval_id}/versions/{version_id}")
async def get_version_evaluator_details(project_id: str, eval_id: str, version_id: str):
    try:
        project = mixedvoices.load_project(project_id)
        current_eval = project.load_evaluator(eval_id)
        eval_runs = current_eval.list_eval_runs(version_id)
        eval_run_data = [eval_run.info for eval_run in eval_runs]

        return {
            "metrics": current_eval.metric_names,
            "test_cases": current_eval.test_cases,
            "eval_runs": eval_run_data,
        }
    except KeyError as e:
        logger.error(
            f"Eval '{eval_id}' or project '{project_id}' or version '{version_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error listing version evals: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/projects/{project_id}/evals/{eval_id}/runs/{run_id}")
async def get_eval_run_details(project_id: str, eval_id: str, run_id: str):
    try:
        project = mixedvoices.load_project(project_id)
        current_eval = project.load_evaluator(eval_id)
        eval_run = current_eval.load_eval_run(run_id)
        return {"results": eval_run.results, "version": eval_run.version_id}
    except KeyError as e:
        logger.error(
            f"Run {run_id} or Eval '{eval_id}' or project '{project_id}' not found: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting eval run details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/prompt_generator")
async def generate_prompt(
    agent_prompt: str,
    user_demographic_info: Optional[str] = None,
    transcript: Optional[str] = None,
    user_channel: Optional[str] = "left",
    description: Optional[str] = None,
    edge_case_count: Optional[int] = None,
    file: Optional[UploadFile] = None,
):
    try:
        temp_dir = None
        test_case_generator = TestCaseGenerator(agent_prompt, user_demographic_info)
        if transcript:
            test_case_generator.add_from_transcripts([transcript])
        elif file:
            temp_path, temp_dir = copy_file_content(file)
            test_case_generator.add_from_recordings([temp_path], user_channel)
        elif description:
            test_case_generator.add_from_descriptions([description])
        elif edge_case_count:
            test_case_generator.add_edge_cases(edge_case_count)
        else:
            raise ValueError(
                "Either transcript, file, description, or edge_case_count must be provided"
            )
        prompts = test_case_generator.generate()
        return {"prompts": prompts}
    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_dir:
            temp_dir.cleanup()


def run_server(port: int = 7760):
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
