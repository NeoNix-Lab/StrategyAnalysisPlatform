# Socket Implementation Guide

This guide provides implementation patterns for using the socket models in the Strategy Analysis Platform.

## 1. WebSocket Server Implementation

### Basic WebSocket Handler
```python
import asyncio
import json
from typing import Dict, Set
from websockets.server import WebSocketServerProtocol
from socket_models import (
    SocketMessage, 
    SocketMessageType, 
    create_ack_message,
    create_error_message
)

class SocketHandler:
    def __init__(self):
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # target -> set of connection_ids
    
    async def register(self, websocket: WebSocketServerProtocol, client_id: str):
        """Register a new client connection"""
        self.connections[client_id] = websocket
        print(f"Client {client_id} connected")
    
    async def unregister(self, client_id: str):
        """Unregister a client connection"""
        if client_id in self.connections:
            del self.connections[client_id]
            # Clean up subscriptions
            for target, subscribers in self.subscriptions.items():
                subscribers.discard(client_id)
            print(f"Client {client_id} disconnected")
    
    async def handle_message(self, websocket: WebSocketServerProtocol, client_id: str, raw_message: str):
        """Handle incoming socket message"""
        try:
            message_data = json.loads(raw_message)
            message = SocketMessage(**message_data)
            
            # Send acknowledgment
            ack = create_ack_message(source="server", original_msg_id=message.msg_id)
            await websocket.send(ack.json())
            
            # Route message based on type
            await self.route_message(message, client_id)
            
        except Exception as e:
            error_msg = create_error_message(
                source="server",
                error_code="INVALID_MESSAGE",
                error_message=str(e)
            )
            await websocket.send(error_msg.json())
    
    async def route_message(self, message: SocketMessage, sender_id: str):
        """Route message to appropriate handlers"""
        if message.msg_type == SocketMessageType.INGEST_EVENT:
            await self.handle_ingest_event(message)
        elif message.msg_type == SocketMessageType.LOG_RECORD:
            await self.handle_log_record(message)
        elif message.msg_type == SocketMessageType.HEARTBEAT:
            await self.handle_heartbeat(message)
        # Add other message types as needed
    
    async def handle_ingest_event(self, message: SocketMessage):
        """Handle ingest event messages"""
        # Process ingest event (store in database, trigger trade reconstruction, etc.)
        print(f"Processing ingest event from {message.source}: {message.payload}")
        
        # Broadcast to relevant subscribers
        await self.broadcast_to_subscribers("ingest_events", message)
    
    async def handle_log_record(self, message: SocketMessage):
        """Handle log record messages"""
        # Process log record (store in log system, forward to log aggregator)
        print(f"Processing log from {message.source}: {message.payload['level']} - {message.payload['message']}")
        
        # Broadcast to log subscribers
        await self.broadcast_to_subscribers("logs", message)
    
    async def handle_heartbeat(self, message: SocketMessage):
        """Handle heartbeat messages"""
        print(f"Heartbeat from {message.source}")
        # Update connection health status
    
    async def broadcast_to_subscribers(self, topic: str, message: SocketMessage):
        """Broadcast message to all subscribers of a topic"""
        if topic in self.subscriptions:
            for connection_id in self.subscriptions[topic]:
                if connection_id in self.connections:
                    try:
                        await self.connections[connection_id].send(message.json())
                    except Exception as e:
                        print(f"Failed to send to {connection_id}: {e}")
    
    async def send_to_client(self, client_id: str, message: SocketMessage):
        """Send message to specific client"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send(message.json())
            except Exception as e:
                print(f"Failed to send to {client_id}: {e}")
```

### WebSocket Server Setup
```python
import websockets
from socket_models import SocketMessage

async def handle_client(websocket: WebSocketServerProtocol, path: str):
    """Handle individual client connection"""
    handler = SocketHandler()  # In real implementation, this would be shared
    client_id = f"client_{id(websocket)}"
    
    await handler.register(websocket, client_id)
    
    try:
        async for message in websocket:
            await handler.handle_message(websocket, client_id, message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await handler.unregister(client_id)

async def main():
    """Start the WebSocket server"""
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Client Implementation

### Quantower Connector Client
```python
import asyncio
import json
import websockets
from socket_models import (
    create_ingest_message,
    create_log_message,
    create_heartbeat_message,
    IngestEventType,
    LogLevel
)

class QuantowerConnector:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket = None
        self.client_id = "quantower-connector"
        self.running = False
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.running = True
            print(f"Connected to {self.server_url}")
            
            # Start message processing loop
            asyncio.create_task(self.process_messages())
            
            # Start heartbeat loop
            asyncio.create_task(self.heartbeat_loop())
            
        except Exception as e:
            print(f"Failed to connect: {e}")
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
    
    async def send_order_event(self, run_id: str, order_data: dict):
        """Send order event to server"""
        message = create_ingest_message(
            source=self.client_id,
            run_id=run_id,
            event_type=IngestEventType.ORDER,
            payload=order_data
        )
        await self.send_message(message)
    
    async def send_execution_event(self, run_id: str, execution_data: dict):
        """Send execution event to server"""
        message = create_ingest_message(
            source=self.client_id,
            run_id=run_id,
            event_type=IngestEventType.EXECUTION,
            payload=execution_data
        )
        await self.send_message(message)
    
    async def send_log(self, level: LogLevel, message: str, meta: dict = None):
        """Send log message to server"""
        log_message = create_log_message(
            source=self.client_id,
            level=level,
            logger_name="quantower_connector",
            message=message,
            meta=meta
        )
        await self.send_message(log_message)
    
    async def send_message(self, message: SocketMessage):
        """Send message to server"""
        if self.websocket:
            try:
                await self.websocket.send(message.json())
            except Exception as e:
                print(f"Failed to send message: {e}")
    
    async def process_messages(self):
        """Process incoming messages from server"""
        while self.running and self.websocket:
            try:
                raw_message = await self.websocket.recv()
                message_data = json.loads(raw_message)
                message = SocketMessage(**message_data)
                
                # Handle server messages (ACK, errors, etc.)
                await self.handle_server_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f"Error processing message: {e}")
    
    async def handle_server_message(self, message: SocketMessage):
        """Handle messages from server"""
        if message.msg_type == SocketMessageType.ACK:
            print(f"Received ACK for message: {message.payload['acknowledged_msg_id']}")
        elif message.msg_type == SocketMessageType.ERROR:
            print(f"Server error: {message.payload['code']} - {message.payload['message']}")
        # Add other message types as needed
    
    async def heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.running:
            try:
                heartbeat = create_heartbeat(source=self.client_id)
                await self.send_message(heartbeat)
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break

# Usage example
async def main():
    connector = QuantowerConnector("ws://localhost:8765")
    await connector.connect()
    
    # Send some test events
    await connector.send_order_event("run-123", {
        "order_id": "ord-test-1",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.1,
        "price": 45000.0
    })
    
    await connector.send_log(LogLevel.INFO, "Connector started successfully")
    
    # Keep running
    try:
        while connector.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. Integration with Trade Service

### Enhanced Trade Service with Socket Support
```python
from socket_models import create_ingest_message, create_log_message, IngestEventType, LogLevel
from typing import Optional

class SocketTradeService:
    def __init__(self, db_session, socket_handler):
        self.db = db_session
        self.socket = socket_handler
    
    async def process_ingest_event(self, message_data: dict):
        """Process ingest event from socket"""
        try:
            run_id = message_data["run_id"]
            event_type = message_data["event_type"]
            payload = message_data["payload_json"]
            
            # Store ingest event in database
            ingest_event = IngestEvent(
                run_id=run_id,
                event_type=event_type,
                event_utc=message_data["event_utc"],
                payload_json=payload,
                received_utc=datetime.utcnow()
            )
            self.db.add(ingest_event)
            self.db.commit()
            
            # Process based on event type
            if event_type == IngestEventType.ORDER:
                await self.process_order_event(run_id, payload)
            elif event_type == IngestEventType.EXECUTION:
                await self.process_execution_event(run_id, payload)
            elif event_type == IngestEventType.MARKET_DATA:
                await self.process_market_data_event(run_id, payload)
            
            # Send success log
            log_msg = create_log_message(
                source="trade_service",
                level=LogLevel.INFO,
                logger_name="ingest_processor",
                message=f"Processed {event_type} event for run {run_id}",
                meta={"event_type": event_type, "run_id": run_id}
            )
            await self.socket.broadcast_to_subscribers("logs", log_msg)
            
        except Exception as e:
            # Send error log
            error_msg = create_log_message(
                source="trade_service",
                level=LogLevel.ERROR,
                logger_name="ingest_processor",
                message=f"Failed to process ingest event: {str(e)}",
                meta={"error": str(e), "event_data": message_data}
            )
            await self.socket.broadcast_to_subscribers("logs", error_msg)
    
    async def process_order_event(self, run_id: str, payload: dict):
        """Process order event"""
        # Create order in database
        order = Order(
            order_id=payload["order_id"],
            run_id=run_id,
            symbol=payload["symbol"],
            side=payload["side"],
            order_type=payload["order_type"],
            quantity=payload["quantity"],
            price=payload.get("price"),
            created_utc=datetime.utcnow()
        )
        self.db.add(order)
        self.db.commit()
        
        # Broadcast order to subscribers
        from socket_models import SocketMessage, SocketMessageType
        order_msg = SocketMessage(
            msg_type=SocketMessageType.INGEST_EVENT,
            source="trade_service",
            payload={
                "event": "order_processed",
                "order_id": order.order_id,
                "run_id": run_id,
                "status": order.status
            }
        )
        await self.socket.broadcast_to_subscribers("orders", order_msg)
    
    async def rebuild_trades_for_run(self, run_id: str):
        """Enhanced trade reconstruction with socket notifications"""
        try:
            # Send start notification
            start_msg = create_log_message(
                source="trade_service",
                level=LogLevel.INFO,
                logger_name="trade_reconstruction",
                message=f"Starting trade reconstruction for run {run_id}",
                meta={"run_id": run_id}
            )
            await self.socket.broadcast_to_subscribers("trades", start_msg)
            
            # Perform trade reconstruction (existing logic)
            # ... existing trade reconstruction code ...
            
            # Send completion notification
            complete_msg = create_log_message(
                source="trade_service",
                level=LogLevel.INFO,
                logger_name="trade_reconstruction",
                message=f"Trade reconstruction completed for run {run_id}",
                meta={"run_id": run_id, "trades_count": len(trades)}
            )
            await self.socket.broadcast_to_subscribers("trades", complete_msg)
            
        except Exception as e:
            error_msg = create_log_message(
                source="trade_service",
                level=LogLevel.ERROR,
                logger_name="trade_reconstruction",
                message=f"Trade reconstruction failed for run {run_id}: {str(e)}",
                meta={"run_id": run_id, "error": str(e)}
            )
            await self.socket.broadcast_to_subscribers("trades", error_msg)
```

## 4. Testing Socket Communication

### Unit Test Example
```python
import pytest
import asyncio
from socket_models import create_ingest_message, IngestEventType, SocketMessage

@pytest.mark.asyncio
async def test_ingest_message_creation():
    """Test ingest message creation and validation"""
    message = create_ingest_message(
        source="test-source",
        run_id="test-run-123",
        event_type=IngestEventType.ORDER,
        payload={"order_id": "test-order", "symbol": "BTCUSDT"}
    )
    
    assert message.msg_type == "ingest_event"
    assert message.source == "test-source"
    assert message.payload["run_id"] == "test-run-123"
    assert message.payload["event_type"] == "order"
    
    # Test JSON serialization
    json_data = message.json()
    parsed_message = SocketMessage.parse_raw(json_data)
    assert parsed_message.msg_id == message.msg_id

@pytest.mark.asyncio
async def test_socket_message_roundtrip():
    """Test message serialization/deserialization"""
    original = create_ingest_message(
        source="quantower",
        run_id="run-456",
        event_type=IngestEventType.EXECUTION,
        payload={"execution_id": "exec-789", "quantity": 1.0}
    )
    
    # Serialize and deserialize
    json_str = original.json()
    restored = SocketMessage.parse_raw(json_str)
    
    assert restored.msg_type == original.msg_type
    assert restored.source == original.source
    assert restored.payload == original.payload
```

This implementation guide provides a complete foundation for real-time socket communication in the Strategy Analysis Platform, with proper error handling, message routing, and integration patterns.
