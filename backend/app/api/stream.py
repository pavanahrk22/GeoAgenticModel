from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # map trip_id to list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trip_id: str):
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)
        logger.info(f"Client connected for trip {trip_id}. Total clients for trip: {len(self.active_connections[trip_id])}")

    def disconnect(self, websocket: WebSocket, trip_id: str):
        if trip_id in self.active_connections:
            if websocket in self.active_connections[trip_id]:
                self.active_connections[trip_id].remove(websocket)
            if not self.active_connections[trip_id]:
                del self.active_connections[trip_id]
        logger.info(f"Client disconnected from trip {trip_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_trip(self, trip_id: str, message: Dict[str, Any]):
        if trip_id in self.active_connections:
            msg_str = json.dumps(message)
            for connection in self.active_connections[trip_id]:
                try:
                    await connection.send_text(msg_str)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    async def broadcast_all(self, message: Dict[str, Any]):
        msg_str = json.dumps(message)
        for trip_connections in self.active_connections.values():
            for connection in trip_connections:
                try:
                    await connection.send_text(msg_str)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

manager = ConnectionManager()

@router.websocket("/stream/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: str):
    await manager.connect(websocket, trip_id)
    try:
        while True:
            # We don't really expect clients to send data, but keep connection open
            data = await websocket.receive_text()
            logger.debug(f"Received data from client {trip_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, trip_id)
