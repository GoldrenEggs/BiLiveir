import asyncio
import inspect
import threading
from collections import defaultdict
from functools import wraps
from logging import Logger
from typing import Callable, Any, TypeVar, Generic, Coroutine, Self, TypeAlias
from dataclasses import dataclass

from src.connect import LiveConnect
from src.decode import decode_packet
from src.log import logger
from src.message import Message

HandlerFunc: TypeAlias = Callable[..., Coroutine]
T_RAW_HANDLER_FUNC = TypeVar('T_RAW_HANDLER_FUNC', bound=HandlerFunc)

T_MESSAGE = TypeVar('T_MESSAGE', bound=Message)
AutoHandlerFunc: TypeAlias = Callable[[T_MESSAGE], Coroutine]


@dataclass
class Handler:
    func: HandlerFunc
    parser: Callable[[dict], Coroutine] | None


class Biliveir:
    def __init__(self, room_id: int):
        self.room_id = room_id
        self.handlers_map: dict[str, list[Handler]] = defaultdict(list)
        self.any_handlers: list[Handler] = []  # 执行任意指令
        self.unregistered_handlers: list[Handler] = []  # 执行未被注册过的指令
        self.logger: Logger | None = logger

    def register(self, cmd: str, parser: Callable[[dict], Any] = None
                 ) -> Callable[[T_RAW_HANDLER_FUNC], T_RAW_HANDLER_FUNC]:
        """
        注册函数（异步）至目标指令下，向目标函数传递原始消息
        :param cmd: 指令
        :param parser: 解析器
        :return: 注册装饰器
        """

        def decorator(handler_func: T_RAW_HANDLER_FUNC) -> T_RAW_HANDLER_FUNC:
            handler = Handler(handler_func, parser)
            if cmd == 'ANY':
                self.any_handlers.append(handler)
            elif cmd == 'UNREGISTERED':
                self.unregistered_handlers.append(handler)
            else:
                self.handlers_map[cmd].append(handler)
            return handler_func

        return decorator

    @staticmethod
    async def _task(handler: Handler, message: dict):
        if handler.parser is not None:
            message = await handler.parser(message)
        await handler.func(message)

    async def run(self):
        """运行Biliveir"""
        async with LiveConnect(self.room_id) as connect:
            async for packet in connect.recv():
                messages = decode_packet(packet)
                for message in messages:  # 为了减少耦合，这一坨嵌套还是不优化为好
                    if 'cmd' not in message:
                        continue
                    cmd: str = message['cmd']
                    if cmd in self.handlers_map:
                        handlers = self.handlers_map[cmd]
                    else:
                        handlers = self.unregistered_handlers
                    for handler in handlers + self.any_handlers:
                        asyncio.create_task(self._task(handler, message))

    def sync_run(self, block: bool = True) -> threading.Thread | None:
        """
        以同步的方法运行Biliveir
        :param block: 是否阻塞
        :return: 若不阻塞则返回子线程句柄
        """
        if block:
            try:
                asyncio.run(self.run())
            except KeyboardInterrupt:  # 优雅退出（真的优雅吗？）
                return
        else:
            handle = threading.Thread(target=asyncio.run, args=(self.run(),), daemon=True)
            handle.start()
            return handle  # 一点点耦合大概是不要紧的


if __name__ == '__main__':
    biliveir = Biliveir(923833)


    @biliveir.register('ANY')
    async def anything(message):
        print(message)


    biliveir.sync_run()
