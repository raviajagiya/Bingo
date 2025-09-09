import asyncio
from typing import Dict, Optional
from .room import BingoRoom
from .utils import generate_room_code
from ..config import ROOM_CODE_LENGTH

class RoomRegistry:
    def __init__(self):
        self.rooms: Dict[str, BingoRoom] = {}
        self.lock = asyncio.Lock()

# Create a new room with a unique code
    async def create_room(self, host_name: str) -> BingoRoom:
        async with self.lock:
            for _ in range(6):
                code = generate_room_code(ROOM_CODE_LENGTH)
                if code not in self.rooms:
                    room = BingoRoom(code, host_name)
                    self.rooms[code] = room
                    return room
            # fallback to longer code if collision persists booooommmmm
            code = generate_room_code(ROOM_CODE_LENGTH + 2)
            room = BingoRoom(code, host_name)
            self.rooms[code] = room
            return room
        
# Retrieve a room by its code
    def get(self, room_id: str) -> Optional[BingoRoom]:
        return self.rooms.get(room_id)

# Remove a room if it has no players
    async def maybe_cleanup(self, room_id: str):
        room = self.rooms.get(room_id)
        if room and not room.players:
            self.rooms.pop(room_id, None)

registry = RoomRegistry()
