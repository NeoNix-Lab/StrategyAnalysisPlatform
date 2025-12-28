import multiprocessing
import time
from typing import Dict, Optional
from datetime import datetime
import traceback
import os

from src.database.connection import SessionLocal
from .runner import TrainingRunner

class JobManager:
    """
    Singleton manager for Training Processes.
    Spawns independent processes for training to avoid blocking the API.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs = {} # Dict[iteration_id, Process]
        return cls._instance

    def start_job(self, iteration_id: str):
        """
        Spawns a new process for the given iteration_id.
        """
        if iteration_id in self.jobs:
            if self.jobs[iteration_id].is_alive():
                raise ValueError(f"Job {iteration_id} is already running")
            else:
                # Cleanup dead process
                del self.jobs[iteration_id]

        # spawn process
        p = multiprocessing.Process(
            target=self._run_worker,
            args=(iteration_id,),
            name=f"TrainingJob-{iteration_id}",
            daemon=True # Daemonize so they die if main process dies (usually safer for dev)
        )
        p.start()
        self.jobs[iteration_id] = p
        return p.pid

    def stop_job(self, iteration_id: str) -> bool:
        """
        Terminates the process for the given iteration_id.
        """
        if iteration_id in self.jobs:
            p = self.jobs[iteration_id]
            if p.is_alive():
                # We first try to set status to CANCELLING in DB so runner can exit gracefully?
                # But here we force kill for immediate stop as requested by M4 "Stop" button.
                # Ideally: Set DB flag -> Wait -> Kill.
                # For now: Just Kill.
                p.terminate() 
                p.join(timeout=1)
                if p.is_alive():
                    p.kill()
                
                # Update status in DB to CANCELED if it wasn't already
                self._mark_as_canceled(iteration_id)
                return True
        return False

    def get_job_status(self, iteration_id: str) -> str:
        if iteration_id in self.jobs:
            p = self.jobs[iteration_id]
            if p.is_alive():
                return "RUNNING"
            else:
                # Process finished, but we don't know if success or specific fail 
                # without checking DB. 
                # But checking DB here is expensive. API should check DB.
                # Start job removes it from this dict? No.
                return "STOPPED" 
        return "UNKNOWN"

    @staticmethod
    def _run_worker(iteration_id: str):
        """
        The entrypoint for the separate process.
        MUST create its own DB session.
        """
        db = SessionLocal()
        try:
            print(f"[JobManager] Starting worker for {iteration_id} (PID: {os.getpid()})")
            
            # Using the existing Runner logic
            runner = TrainingRunner(db, iteration_id)
            runner.run()
            
        except Exception as e:
            print(f"[JobManager] Worker Fatal Error: {e}")
            traceback.print_exc()
            # Try to log failure to DB if possible
            # (Runner usually handles its own exceptions, so this is catch-all)
        finally:
            db.close()
            print(f"[JobManager] Worker finished {iteration_id}")

    def _mark_as_canceled(self, iteration_id: str):
        """
        Failsafe to ensure DB reflects cancellation if we force-killed the process.
        """
        db = SessionLocal()
        try:
            # Avoid circular imports if possible, look up model dynamically or import inside
            from src.database.models import MlIteration
            
            iteration = db.query(MlIteration).get(iteration_id)
            if iteration and iteration.status in ["PENDING", "RUNNING"]:
                iteration.status = "CANCELED"
                iteration.end_utc = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"Error marking job as canceled: {e}")
        finally:
            db.close()

# Global accessor
job_manager = JobManager()
