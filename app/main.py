from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .config import APP_NAME, ORIGINS
from .routers.rooms import router as rooms_router, handle_ws

app = FastAPI(title=APP_NAME)

# CORS for Android emulator/device testing
if ORIGINS == ["*"]:
    allow_origins = ["*"]
else:
    allow_origins = ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Delegate to rooms handler
    await handle_ws(ws)
