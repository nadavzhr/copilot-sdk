"""Background job management tools."""

import os
import signal

from pydantic import BaseModel, Field

from copilot import define_tool

from registry.job_registry import JobRegistry


class JobIdParams(BaseModel):
    """Parameters for job operations requiring a job ID."""

    job_id: str = Field(description="The job ID to operate on")


@define_tool(description="List all background jobs and their status")
async def list_background_jobs() -> dict:
    """Get all registered background jobs.

    Returns:
        Dictionary containing list of jobs, total count, and running count.
    """
    registry = JobRegistry()
    jobs = registry.list_jobs()

    # Update status for each job
    for job in jobs:
        job["is_running"] = registry.is_job_running(job["pid"])

    return {
        "jobs": jobs,
        "total": len(jobs),
        "running": sum(1 for j in jobs if j["is_running"]),
    }


@define_tool(description="Get detailed status of a specific background job")
async def get_job_status(params: JobIdParams) -> dict:
    """Get status of a specific job.

    Args:
        params: Parameters containing the job ID.

    Returns:
        Dictionary with job details and running status, or error if not found.
    """
    registry = JobRegistry()
    job = registry.get_job(params.job_id)

    if not job:
        return {"error": f"Job {params.job_id} not found"}

    job["is_running"] = registry.is_job_running(job["pid"])
    return job


@define_tool(description="Stop/kill a background job by its ID")
async def stop_background_job(params: JobIdParams) -> dict:
    """Stop a running background job.

    Args:
        params: Parameters containing the job ID.

    Returns:
        Dictionary with success status and message, or error details.
    """
    registry = JobRegistry()
    job = registry.get_job(params.job_id)

    if not job:
        return {"error": f"Job {params.job_id} not found"}

    try:
        os.kill(job["pid"], signal.SIGTERM)
        registry.update_job_status(params.job_id, "stopped")
        return {
            "success": True,
            "message": f"Job {params.job_id} (PID {job['pid']}) stopped",
        }
    except ProcessLookupError:
        registry.update_job_status(params.job_id, "not_found")
        return {"error": "Process not found - may have already exited"}
    except Exception as e:
        return {"error": str(e)}


@define_tool(description="Remove a job from the registry (cleanup)")
async def remove_job(params: JobIdParams) -> dict:
    """Remove a job from the registry.

    Args:
        params: Parameters containing the job ID.

    Returns:
        Dictionary with success status and appropriate message.
    """
    registry = JobRegistry()
    success = registry.remove_job(params.job_id)
    return {
        "success": success,
        "message": f"Job {params.job_id} removed" if success else "Job not found",
    }
