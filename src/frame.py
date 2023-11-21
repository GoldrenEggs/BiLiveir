import asyncio
import threading
from collections import defaultdict
from functools import wraps
from typing import Callable, Any, TypeVar, Generic, Coroutine, Self

from src.connect import LiveConnect
from src.decode import decode_packet


class Biliveir:
    def __init__(self, room_id: int):
        self.handlers = defaultdict(list)
        self.live_connect = LiveConnect(room_id)

    def add_handle(self, cmd: str, handler: Callable[[dict], Coroutine]) -> Self:
        self.handlers[cmd].append(handler)
        return self

    def register(self, cmd: str) -> Callable[[Callable], Callable]:
        """
        注册函数（异步）至目标指令下，向目标函数传递原始消息
        :param cmd: 指令
        :return: 注册装饰器
        """

        def decorator(handler: Callable[[dict], Coroutine]):
            self.add_handle(cmd, handler)
            return handler

        return decorator

    async def run(self):
        """运行Biliveir"""
        await self.live_connect.connect()
        async for packet in self.live_connect.recv():
            messages = decode_packet(packet)
            for message in messages:
                if 'cmd' not in messages:
                    continue
                cmd = message['cmd']
                for func in self.handlers[cmd]:
                    asyncio.create_task(func(message))

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
    biliveir = Biliveir(8641)


    async def alpha():
        ...


    biliveir.add_handle('avc', alpha)


    @biliveir.register('DANMU_MSG')
    async def danmu(message):
        print(message)


    biliveir.sync_run()
