from aiowebsocket.converses import AioWebSocket, Converse

from src.packet import AuthPacket, HeartbeatPacket, AuthData, HeartbeatData


class LiveConnect:
    URI = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

    def __init__(self, room_id: int):
        self.room_id = room_id
        self.sequence = 0
        self.aws = AioWebSocket(self.URI)

    async def send_auth_packet(self):
        self.sequence += 1
        packet = AuthPacket(self.sequence, AuthData(self.room_id))

    async def connect(self):
        await self.aws.create_connection()
        await self.aws.converse


if __name__ == '__main__':
    import asyncio

    asyncio.run(LiveConnect(8641).connect())
