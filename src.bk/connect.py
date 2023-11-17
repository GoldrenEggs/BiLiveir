import asyncio
import json
import zlib
from struct import pack, unpack
from typing import Optional, List

from aiowebsocket.converses import AioWebSocket, Converse


class Header:
    """
    数据头, 提供简单的解析方法
    """
    INDEX = [4, 6, 8, 12, 16]
    NAMES = ['总长度', '头部长度', '协议', '操作码', 'sequence']

    def __init__(self, header: bytes):
        if len(header) < 16:
            raise ValueError(f'文件头长度不足16位，当前长度：{len(header)}，内容：{header}')
        self.header_list = [header[0 if e == 0 else self.INDEX[e - 1]: i] for e, i in enumerate(self.INDEX)]

    def __getitem__(self, item: int) -> int:
        temp = self.header_list[item]
        return unpack('>i' if len(temp) == 4 else '>h', temp)[0]

    def __str__(self):
        string_list = []
        for i in range(5):
            if i in (0, 3, 4):
                string_list.append(f'{self.NAMES[i]}:{unpack(">i", self.header_list[i])[0]}')
            else:
                string_list.append(f'{self.NAMES[i]}:{unpack(">h", self.header_list[i])[0]}')
        return ', '.join(string_list)


class LiveConnect:
    uri = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

    def __init__(self, room_id):
        self.room_id = room_id
        self.sequence = 0
        self.converse: Optional[Converse] = None

    @staticmethod
    def _decode_msg(message: bytes) -> List[bytes]:
        msg_list = []

        def recursion(msg: bytes):
            header = Header(msg[:16])
            if header[0] != len(msg):  # 同时多个包，依次解析
                recursion(msg[:header[0]])
                recursion(msg[header[0]:])
                return
            if header[3] == 3:  # 心跳包回复，封装成普通包
                msg_list.append(b'\x00\x00\00\x00' + msg[4:16] + b'{"cmd":"HEART_BEAT_REPLY","data":'
                                + bytes(str(unpack('>i', msg[16:])[0]), encoding='utf-8') + b'}')
            elif header[3] == 5:  # 压缩包，解压后解析
                match header[2]:
                    case 0:
                        msg_list.append(msg)
                    case 2:
                        recursion(zlib.decompress(msg[16:]))
                    case _:
                        print('未知的压缩方法')
            elif header[3] == 8:  # 认证包回复，封装成普通包
                msg_list.append(b'\x00\x00\x00\x00' + msg[4:16] + b'{"cmd":"AUTH_REPLY","data":' + msg[16:] + b'}')

        recursion(message)
        return msg_list

    def _encode(self, msg: str, operation_code: int) -> bytes:
        """
        为消息添加消息头并编码为二进制
        :param msg: 消息内容
        :param operation_code: 操作码  2:心跳包  3:心跳包回复  5:普通包  7:认证包  8:认证包回复
        :return: 编码好的传递内容
        """
        data = msg.encode('utf-8')
        packet_len = pack('>i', 16 + len(data))
        return packet_len + b'\x00\x10\x00\x00' + pack('>i', operation_code) + pack('>i', self.sequence) + data

    async def send_auth_pack(self) -> bytes:
        self.sequence += 1
        message = json.dumps({'room_id': self.room_id})
        await self.converse.send(self._encode(message, 7))
        result: bytes = await self.converse.receive()
        print(result)
        return result[16:]

    async def send_heartbeat_pack(self):
        """
        发送心跳包
        """
        await asyncio.sleep(3)
        while True:
            self.sequence += 1
            message = ''
            await self.converse.send(self._encode(message, 2))
            await asyncio.sleep(30)

    async def recv(self):
        await asyncio.sleep(2)
        while True:
            r = await self.converse.message_queue.get()
            msg_list = self._decode_msg(r)
            for msg in msg_list:
                m = str(msg[16:], encoding='utf-8')
                yield json.loads(m)

    async def connect(self):
        aws = AioWebSocket(self.uri)
        await aws.create_connection()
        try:
            self.converse = aws.manipulator
            if not await self.send_auth_pack():
                raise BiLiveAuthError('认证失败')
            await self.send_heartbeat_pack()
        except KeyboardInterrupt:
            await aws.close_connection()

    async def loop_print_recv(self):
        async for msg in self.recv():
            print(msg)

    async def start(self):
        await asyncio.gather(self.connect(), self.loop_print_recv())


class BiLiveAuthError(Exception):
    pass


if __name__ == '__main__':
    live = LiveConnect(8641)
    asyncio.run(live.start())
