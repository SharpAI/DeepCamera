import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from backend.config import settings

router = APIRouter(tags=["websocket"])

# Active WebSocket connections
_connections: set[WebSocket] = set()


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """Real-time incident alert stream via Redis pub/sub."""
    await websocket.accept()
    _connections.add(websocket)
    try:
        async with aioredis.from_url(settings.REDIS_URL) as r:
            pubsub = r.pubsub()
            await pubsub.subscribe("namucam:alerts")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    await websocket.send_text(data)
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(websocket)
