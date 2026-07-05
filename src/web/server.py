import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.core.controller import EngineController
from src.core.database import get_recent_intercepts

app = FastAPI(title="KiwiSDR AI Listener Dashboard")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

clients = set()
loop = None

def broadcast_event(event_type: str, payload: dict):
    if not loop:
        return
        
    msg = json.dumps({"event": event_type, "data": payload})
    for client in clients:
        asyncio.run_coroutine_threadsafe(client.send_text(msg), loop)

engine = EngineController(use_mock=False, event_callback=broadcast_event)

@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_running_loop()

@app.on_event("shutdown")
async def shutdown_event():
    engine.stop()

@app.get("/")
async def get_index():
    return FileResponse("src/web/static/index.html")

@app.post("/api/start")
async def start_engine(mock: bool = False):
    if engine.running:
        return {"status": "already running"}
    engine.use_mock = mock
    engine.start()
    return {"status": "started"}

@app.post("/api/stop")
async def stop_engine():
    engine.stop()
    return {"status": "stopped"}

@app.get("/api/status")
async def get_status():
    return {
        "running": engine.running,
        "mode": "mock" if engine.use_mock else "live",
        "node": engine.current_node.name if engine.current_node else None,
        "frequency": engine.tuner.current_params.get("frequency") if engine.tuner else None
    }

@app.get("/api/history")
async def get_history():
    return get_recent_intercepts(limit=100)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)
