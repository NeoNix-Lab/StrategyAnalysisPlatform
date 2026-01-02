from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import logging
import json
from datetime import datetime
from quant_shared.utils.logger import attach_queue_handler, get_logger
# Try to import from contracts, might need path adjustment in dev
try:
    from contracts.logging.models import LogRecord
except ImportError:
    # If contracts package not installed in env, we might need to add it to sys.path or fail
    # For now, we assume it's available or we add a mocked fallback for safety if user hasn't installed it yet
    import sys
    import os
    # Try adding standard location relative to this file
    # d:\Documents\Active\StrategyAnalysisPlatform\Main\services\api_gateway\src\api\routers\system.py
    # -> ../../../../../packages
    current_dir = os.path.dirname(os.path.abspath(__file__))
    packages_dir = os.path.abspath(os.path.join(current_dir, "../../../../../packages"))
    if packages_dir not in sys.path:
        sys.path.append(packages_dir)
    from contracts.logging.models import LogRecord

router = APIRouter()
logger = get_logger("system_router")

# Global Log Queue
# We uses asyncio.Queue for async compatibility in FastAPI
log_queue = asyncio.Queue()

# Attach the queue to the root logger or specific loggers so they populate it
# Note: In a multiprocess setup (gunicorn workers), this only captures logs from the current worker.
# For a full microservice distributed logging, we'd need Redis PubSub or similar.
# For this "monolithic" API Gateway dev phase, this works for capturing main process logs.
root_logger = logging.getLogger()
attach_queue_handler(root_logger, log_queue)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.broadcaster_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected to Log Stream. Total: {len(self.active_connections)}")
        
        # Start broadcaster if not running
        if not self.broadcaster_task or self.broadcaster_task.done():
            self.broadcaster_task = asyncio.create_task(self.broadcast_logs())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast_logs(self):
        """
        Consumes the log_queue and sends messages to all connected clients.
        """
        logger.info("Starting Log Broadcaster Loop")
        try:
            while True:
                # Wait for next log record
                record = await log_queue.get()
                
                if not self.active_connections:
                    continue

                # Format record using Contract
                try:
                    # Map logging.LogRecord to contracts.LogRecord
                    # We handle the potential missing fields or differences
                    contract_record = LogRecord(
                        timestamp=datetime.fromtimestamp(record.created),
                        level=record.levelname,
                        name=record.name,
                        message=record.getMessage(),
                        meta={
                            "filename": record.filename,
                            "lineno": record.lineno,
                            "funcName": record.funcName
                        }
                    )
                    
                    log_entry = json.loads(contract_record.json())
                    
                except Exception as e:
                    # Fallback if contract validation fails
                    logger.error(f"Failed to convert log to contract: {e}")
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "ERROR",
                        "name": "system",
                        "message": f"Log conversion error: {str(e)}"
                    }

                # Broadcast
                for connection in list(self.active_connections):
                    try:
                        await connection.send_json(log_entry)
                    except Exception as e:
                        self.disconnect(connection)
                        
        except asyncio.CancelledError:
            logger.info("Log Broadcaster Cancelled")

manager = ConnectionManager()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep connection open. 
            # Client might send "ping" or control messages.
            data = await websocket.receive_text()
            # If needed handle client commands like "pause", "clear" filter, etc.
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
