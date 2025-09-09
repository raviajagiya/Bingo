from pydantic import BaseModel, Field

# Body for creating a new room
class CreateRoomBody(BaseModel):
    host_name: str = Field(min_length=1, max_length=24)

# Response after creating a new room
class CreateRoomResponse(BaseModel):
    room_id: str

# Header for WebSocket connection parameters
class RoomState(BaseModel):
    type: str = "room_state"
    room_id: str
    players: list[str]
    host: str
    status: str
    draw_history: list[int]
