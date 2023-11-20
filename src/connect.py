import asyncio
from typing import Generator

import websockets

from src.packet import MQPacket, AuthPacket, HeartbeatPacket, AuthData, HeartbeatData


class AuthException(Exception):
    ...


class LiveConnect:
    URI = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

    def __init__(self, room_id: int):
        self.room_id = room_id
        self.sequence = 0
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self.heartbeat_task: asyncio.Task | None = None

    async def recv(self) -> Generator[MQPacket, None, None]:
        while self.websocket is not None:
            message = await self.websocket.recv()
            yield MQPacket.unpack(message)

    async def authentication(self):
        self.sequence += 1
        packet = AuthPacket(self.sequence, AuthData(self.room_id)).pack()
        if self.websocket is None:
            raise RuntimeError('WebSocket is not connected')
        await self.websocket.send(packet)
        reply = await self.websocket.recv()
        reply = MQPacket.unpack(reply)
        if reply.data != b'{"code":0}':
            raise AuthException('Authentication failed')

    async def heartbeat(self):
        packet = HeartbeatPacket(self.sequence, HeartbeatData('')).pack()
        while self.websocket is not None:
            self.sequence += 1
            await self.websocket.send(packet)
            print('send heartbeat', self.sequence)
            await asyncio.sleep(30)

    async def connect(self):
        self.websocket = await websockets.connect(self.URI)
        await self.authentication()
        self.heartbeat_task = asyncio.create_task(self.heartbeat())

    async def close(self):
        if self.heartbeat_task is not None:
            self.heartbeat_task.cancel()
        if self.websocket is not None:
            await self.websocket.close()


if __name__ == '__main__':
    async def main():
        lll = LiveConnect(8641)
        await lll.connect()
        async for msg in lll.recv():
            print(msg.__dict__)


    asyncio.run(main())
