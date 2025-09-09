import asyncio
import random
import time
from typing import Dict, List, Set, Optional
from fastapi import WebSocket

class Player:
    def __init__(self, name: str, ws: WebSocket):
        self.name = name
        self.ws = ws
        self.joined_at = time.time()

class BingoRoom:
    def __init__(self, room_id: str, host_name: str):
        self.room_id = room_id
        self.host_name = host_name
        self.players: Dict[str, Player] = {}
        self.status: str = "waiting"  # states : waiting | started | finished
        self.draw_pool: List[int] = list(range(1, 76))
        self.draw_history: List[int] = []
        self.lock = asyncio.Lock()
        self.winners: Set[str] = set()

    def room_state(self):
        return {
            "type": "room_state",
            "room_id": self.room_id,
            "players": list(self.players.keys()),
            "host": self.host_name,
            "status": self.status,
            "draw_history": self.draw_history,
        }

    async def broadcast(self, message: dict):
        stale = []
        for name, player in self.players.items():
            try:
                await player.ws.send_json(message)
            except Exception:
                stale.append(name)
        for name in stale:
            self.players.pop(name, None)

    # Add a new player to the room
    async def add_player(self, name: str, ws: WebSocket):
        self.players[name] = Player(name, ws)
        await self.broadcast({"type": "player_joined", "name": name, "players": list(self.players.keys())})
        await ws.send_json(self.room_state())

    async def remove_player(self, name: str):
        if name in self.players:
            self.players.pop(name, None)
            await self.broadcast({"type": "player_left", "name": name, "players": list(self.players.keys())})

    async def start_game(self, requester: str):
        if requester != self.host_name:
            raise PermissionError("Only host can start the game")
        async with self.lock:
            if self.status != "waiting":
                return
            self.status = "started"
            random.shuffle(self.draw_pool)
        await self.broadcast({"type": "game_started", "draw_history": self.draw_history})

    async def draw_number(self, requester: str):
        if requester != self.host_name:
            raise PermissionError("Only host can draw numbers")
        async with self.lock:
            if self.status != "started":
                raise RuntimeError("Game not started")
            if not self.draw_pool:
                self.status = "finished"
                await self.broadcast({"type": "game_finished", "draw_history": self.draw_history})
                return None
            n = self.draw_pool.pop()
            self.draw_history.append(n)
        await self.broadcast({"type": "number_drawn", "number": n, "history": self.draw_history})
        return n

    async def handle_bingo_claim(self, name: str, card: Optional[List[List[int]]] = None):
        if name in self.winners:
            if name in self.players:
                await self.players[name].ws.send_json({"type": "error", "message": "Already declared"})
            return
        self.winners.add(name)
        self.status = "finished"
        await self.broadcast({"type": "bingo_valid", "name": name, "history": self.draw_history})
        await self.broadcast({"type": "game_finished", "winners": list(self.winners)})
