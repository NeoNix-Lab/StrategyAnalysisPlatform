from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import logging
from quant_shared.utils.logger import attach_queue_handler, get_logger

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
                    # If no one listening, just drain queue effectively or pause?
                    # For now we keep draining to avoid memory leak if queue gets full (unbounded though)
                    continue

                # Format record
                # We assume QueueHandler put a LogRecord object
                # We manually format it to string/JSON
                log_entry = {
                    "timestamp": record.asctime if hasattr(record, "asctime") else record.created,
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage()
                }

                # Broadcast
                # Copy list to avoid modification during iteration
                for connection in list(self.active_connections):
                    try:
                        await connection.send_json(log_entry)
                    except Exception as e:
                        # Handle stale connection
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
