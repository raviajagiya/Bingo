from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from ..models.schemas import CreateRoomBody, CreateRoomResponse
from ..services.registry import registry

router = APIRouter(prefix="/room", tags=["rooms"])

# Create a new room
@router.post("", response_model=CreateRoomResponse)
async def create_room(body: CreateRoomBody):
    room = await registry.create_room(body.host_name)
    return CreateRoomResponse(room_id=room.room_id)


# Validate and return room state
@router.get("/{room_id}")
async def get_room(room_id: str):
    room = registry.get(room_id.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return JSONResponse(room.room_state())

# WebSocket endpoint for room interactions
async def handle_ws(ws: WebSocket):
    await ws.accept()
    try:
        query = ws.scope.get("query_string", b"").decode()
        params = dict(q.split("=", 1)for q in query.split("&") if "=" in q)
        room_id = params.get("room_id", "").upper()
        player_name = params.get("player_name", "") # must be unique within room
        # Basic validation
        if not room_id or not player_name:
            await ws.send_json({"type": "error", "message": "Missing room_id or player_name"})
            await ws.close()
            return
        room = registry.get(room_id)

        # Room existence and name uniqueness check
        if not room:
            await ws.send_json({"type": "error", "message": "Room not found"})
            await ws.close()
            return
        if player_name in room.players:
            await ws.send_json({"type": "error", "message": "Name already taken in this room"})
            await ws.close()
            return

        await room.add_player(player_name, ws)

        # Main message loop
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")
            # Handle different message types
            try:
                if msg_type == "start_game":
                    await room.start_game(player_name)
                elif msg_type == "draw_number":
                    await room.draw_number(player_name)
                elif msg_type == "bingo_claim":
                    await room.handle_bingo_claim(player_name, data.get("card"))
                elif msg_type == "chat":
                    text = data.get("text", "")
                    await room.broadcast({"type": "chat", "from": player_name, "text": text})
                elif msg_type == "get_state":
                    await ws.send_json(room.room_state())
                else:
                    await ws.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})
            except PermissionError as e:
                await ws.send_json({"type": "error", "message": str(e)})
            except RuntimeError as e:
                await ws.send_json({"type": "error", "message": str(e)})
            except Exception:
                await ws.send_json({"type": "error", "message": "Server error"})
    except WebSocketDisconnect: 
        try:
            query = ws.scope.get("query_string", b"").decode()
            params = dict(q.split("=", 1) for q in query.split("&") if "=" in q)
            room_id = params.get("room_id", "").upper()
            player_name = params.get("player_name", "")
            room = registry.get(room_id) if room_id else None
            if room and player_name:
                await room.remove_player(player_name)
                await registry.maybe_cleanup(room_id)
        except Exception:
            pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
