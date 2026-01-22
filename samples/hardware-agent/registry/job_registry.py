"""Background job registry for tracking long-running processes."""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

from agent.config import JOB_REGISTRY_FILE


class JobRegistry:
    """Singleton registry for tracking background jobs.

    This registry maintains a persistent record of background processes
    started by the agent, allowing for status tracking and management.

    Attributes:
        _instance: Singleton instance of the registry.
        _jobs: Dictionary mapping job IDs to job metadata.
    """

    _instance: Optional["JobRegistry"] = None
    _jobs: dict = {}

    def __new__(cls) -> "JobRegistry":
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load jobs from disk."""
        if os.path.exists(JOB_REGISTRY_FILE):
            try:
                with open(JOB_REGISTRY_FILE, "r") as f:
                    self._jobs = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._jobs = {}
        else:
            self._jobs = {}

    def _save(self) -> None:
        """Persist jobs to disk."""
        with open(JOB_REGISTRY_FILE, "w") as f:
            json.dump(self._jobs, f, indent=2, default=str)

    def register_job(
        self,
        pid: int,
        name: str,
        command: str,
        session_id: str,
    ) -> str:
        """Register a new background job.

        Args:
            pid: Process ID of the background job.
            name: Friendly name for the job.
            command: The command that was executed.
            session_id: ID of the session that started the job.

        Returns:
            The unique job ID for tracking.
        """
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        self._jobs[job_id] = {
            "job_id": job_id,
            "pid": pid,
            "name": name,
            "command": command,
            "session_id": session_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "stopped_at": None,
        }

        self._save()
        return job_id

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get a job by ID.

        Args:
            job_id: The unique job identifier.

        Returns:
            Job metadata dictionary or None if not found.
        """
        return self._jobs.get(job_id)

    def list_jobs(self) -> list:
        """List all registered jobs.

        Returns:
            List of all job metadata dictionaries.
        """
        return list(self._jobs.values())

    def update_job_status(self, job_id: str, status: str) -> None:
        """Update the status of a job.

        Args:
            job_id: The unique job identifier.
            status: New status (e.g., 'running', 'stopped', 'completed', 'failed').
        """
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            if status in ("stopped", "completed", "failed"):
                self._jobs[job_id]["stopped_at"] = datetime.now().isoformat()
            self._save()

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the registry.

        Args:
            job_id: The unique job identifier.

        Returns:
            True if job was removed, False if not found.
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save()
            return True
        return False

    def is_job_running(self, pid: int) -> bool:
        """Check if a process is still running.

        Args:
            pid: Process ID to check.

        Returns:
            True if process is running, False otherwise.
        """
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False
