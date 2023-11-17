import asyncio
import json
import zlib
import queue
from traceback import print_exc
from functools import wraps
from time import sleep
from threading import Thread
from typing import Callable, Any
from struct import pack, unpack
from collections import defaultdict

import websocket

from .log import Log, void_loger
from .messages import *


class Header:
    """
    数据头, 提供简单的解析方法
    """
    INDEX = (4, 6, 8, 12, 16)
    NAMES = ('总长度', '头部长度', '协议', '操作码', 'sequence')

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


class LiveMessage:

    def __init__(self, room_id, logger: Log):
        self.room_id = room_id
        self.logger = logger
        self.webs = websocket.create_connection("ws://broadcastlv.chat.bilibili.com:2244/sub")
        self.sequence = 0

    def encode(self, msg: str, operation_code: int) -> bytes:
        """
        为消息添加消息头并编码为二进制
        :param msg: 消息内容
        :param operation_code: 操作码  2:心跳包  3:心跳包回复  5:普通包  7:认证包  8:认证包回复
        :return: 编码好的传递内容
        """
        data = msg.encode('utf-8')
        packet_len = pack('>i', 16 + len(data))
        return packet_len + b'\x00\x10\x00\x00' + pack('>i', operation_code) + pack('>i', self.sequence) + data

    def decode_msg(self, message: bytes) -> list:
        msg_list = []

        def iterate_msg(msg: bytes):
            header = Header(msg[:16])
            if header[0] != len(msg):
                iterate_msg(msg[:header[0]])
                iterate_msg(msg[header[0]:])
                return
            if header[3] == 3:
                msg_list.append(b'\x00\x00\00\x00' + msg[4:16] + b'{"cmd":"HEART_BEAT_REPLY","data":'
                                + bytes(str(unpack('>i', msg[16:])[0]), encoding='utf-8') + b'}')
            elif header[3] == 5:
                match header[2]:
                    case 0:
                        msg_list.append(msg)
                    case 2:
                        iterate_msg(zlib.decompress(msg[16:]))
                    case _:
                        self.logger.warn('未知压缩方式')
            elif header[3] == 8:
                msg_list.append(b'\x00\x00\x00\x00' + msg[4:16] + b'{"cmd":"AUTH_REPLY","data":' + msg[16:] + b'}')

        iterate_msg(message)
        return msg_list

    def send_auth(self):
        """
        发送认证包
        """
        self.sequence += 1
        message = json.dumps({'roomid': self.room_id})
        self.logger.debug('[发送认证包]' + message)
        self.webs.send(self.encode(message, 7))
        result = self.webs.recv()
        self.logger.debug('[认证包回复]' + str(result[16:]))
        return result[16:]

    def send_heartbeat(self):
        """
        发送心跳包
        """
        sleep(3)
        while True:
            self.sequence += 1
            message = ''
            self.logger.debug('[发送心跳包]' + message)
            self.webs.send(self.encode(message, 2))
            sleep(30)

    def connect(self) -> bool:
        if self.send_auth() == b'{"code":0}':
            Thread(target=self.send_heartbeat, daemon=True).start()
            return True
        else:
            return False

    def recv_msg(self):
        message = self.webs.recv()
        return [json.loads(str(msg[16:], encoding='utf-8')) for msg in self.decode_msg(message)]


class Live:
    def __init__(self, room_id: int, logger: Log = void_loger):
        self.logger = logger
        self.msg_pool = queue.Queue(500)
        self._coroutines = defaultdict(list)
        self.web = LiveMessage(room_id, logger)
        self.logger.debug(f"=======任务开始，房间号:{room_id}=======")

    def _run_crawler(self):
        self.web.connect()

        def put_to_pool():
            while True:
                msgs = self.web.recv_msg()
                for msg in msgs:
                    if self.msg_pool.not_full:
                        self.msg_pool.put(msg, block=False)

        Thread(target=put_to_pool, daemon=True).start()

    def _run_coroutine(self):
        loop = asyncio.new_event_loop()
        Thread(target=loop.run_forever, daemon=True).start()

        def get_from_pool():
            while True:
                msg = self.msg_pool.get(block=True)
                cmd = msg.get('cmd')
                coro_list = self._coroutines[cmd] + self._coroutines[''] or self._coroutines['UNREGISTERED']
                for coro in coro_list:
                    asyncio.run_coroutine_threadsafe(coro(msg), loop)

        Thread(target=get_from_pool, daemon=True).start()

    def run(self, block=True):
        self._run_crawler()
        self._run_coroutine()
        while block and input() not in ('q', 'quit', 'exit'):
            pass
        return self

    def _error_report(self, func):
        @wraps(func)
        async def wrap(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                self.logger.error(f'{func} {repr(exc)}')
                print_exc()
                print()

        return wrap

    def to_coroutine(self, func):
        @wraps(func)
        async def wrap(*args, **kwargs):
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return func
        else:
            self.logger.warn(f'{func} 请尽量使用异步函数')
            return wrap

    def register(self, cmd: str = '') -> Callable[[Callable[[dict], Any]], Callable[[dict], Any]]:
        """
        自定义CMD解析方法,不填为解析所有方法
        :param cmd: 包的CMD
        """

        def set_decorators(func: Callable[[dict], Any]) -> Callable[[dict], Any]:
            function = self.to_coroutine(func)
            self._coroutines[cmd].append(self._error_report(function))
            return func

        return set_decorators

    def all(self, func: Callable[[dict], Any]):
        function = self.to_coroutine(func)
        self._coroutines[''].append(self._error_report(function))
        return func

    def unregistered(self, func: Callable[[dict], Any]):
        function = self.to_coroutine(func)
        self._coroutines['UNREGISTERED'].append(self._error_report(function))
        return func

    def heart_beat_reply(self, func: Callable[[HeartBeatReply], Any]):
        function = self.to_coroutine(func)

        @wraps(func)
        async def register_func(data: dict):
            return await function(HeartBeatReply(data))

        self._coroutines['HEART_BEAT_REPLY'].append(self._error_report(register_func))
        return register_func

    def danmu_msg(self, func: Callable[[DanmuMsg], Any]):
        function = self.to_coroutine(func)

        @wraps(func)
        async def register_func(data: dict):
            return await function(DanmuMsg(data))

        self._coroutines['DANMU_MSG'].append(self._error_report(register_func))
        return register_func

    def super_chat_message(self, func: Callable[[SuperChatMessage], Any]):
        function = self.to_coroutine(func)

        @wraps(func)
        async def register_func(data: dict):
            return await function(SuperChatMessage(data))

        self._coroutines['SUPER_CHAT_MESSAGE'].append(self._error_report(register_func))
        return register_func

    def entry_effect(self, func: Callable[[EntryEffect], Any]):
        function = self.to_coroutine(func)

        @wraps(func)
        async def register_func(data: dict):
            return await function(EntryEffect(data))

        self._coroutines['ENTRY_EFFECT'].append(self._error_report(register_func))
        return register_func

    def danmu_aggregation(self, func: Callable[[DanmuAggregation], Any]):
        function = self.to_coroutine(func)

        @wraps(func)
        async def register_func(data: dict):
            return await function(DanmuAggregation(data))

        self._coroutines['DANMU_AGGREGATION'].append(self._error_report(register_func))
        return register_func
