import asyncio
from typing import Generator

import websockets

from src.packet import MqPacket, AuthPacket, HeartbeatPacket, AuthData, HeartbeatData
from src.decode import decode_packet
from src.log import logger


class AuthException(Exception):
    pass


class LiveConnect:
    URI = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

    def __init__(self, room_id: int):
        self.room_id = room_id
        self._sequence = 0
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self._heartbeat_task: asyncio.Task | None = None

    async def recv(self) -> Generator[bytes, None, None]:
        while self.websocket is not None:
            yield await self.websocket.recv()

    async def _authentication(self):
        self._sequence += 1
        packet = AuthPacket(self._sequence, AuthData(self.room_id)).pack()
        if self.websocket is None:
            raise RuntimeError('WebSocket is not connected')
        await self.websocket.send(packet)
        reply = await self.websocket.recv()
        reply = MqPacket.unpack(reply)
        if reply.data != b'{"code":0}':
            raise AuthException('Authentication failed')

    async def _heartbeat(self):
        packet = HeartbeatPacket(self._sequence, HeartbeatData('')).pack()
        while self.websocket is not None:
            self._sequence += 1
            await self.websocket.send(packet)
            await asyncio.sleep(30)

    async def connect(self):
        self.websocket = await websockets.connect(self.URI)
        await self._authentication()
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def close(self):
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        if self.websocket is not None:
            await self.websocket.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


if __name__ == '__main__':
    async def main():
        async with LiveConnect(31363850) as lll:
            async for msg in lll.recv():
                print(msg)


    asyncio.run(main())
