import asyncio
import json
import random

import requests

from log import BaseLog


class LivePusher:
    REQUEST_HEADERS = {
        "Referer": "https://www.bilibili.com",
        "User-Agent": "Mozilla/5.0"
    }

    def __init__(self, logger: BaseLog, *uids: int):
        self._uids: dict = {}
        if uids is not None:
            for uid_item in uids:
                self._uids[uid_item] = 0
        self._logger = logger

    async def _request(self, method: str,
                       url: str,
                       params: dict = None) -> dict:
        return json.loads(requests.request(
            method=method,
            url=url,
            params=params,
            headers=self.REQUEST_HEADERS).text)

    async def __get_user_info(self, uid: int, func=None) -> dict:
        data = (await self._request("GET", "https://api.bilibili.com/x/space/acc/info", {"mid": uid})
                )["data"]
        if func is not None:
            func(data)
        return data

    async def __get_live_status(self, uid: int) -> int:
        return (await self.__get_user_info(uid))["live_room"]["liveStatus"]

    async def __pusher(self, func):
        while True:
            await asyncio.sleep(random.randint(3, 5))
            for uid_item in self._uids:
                live_status = await self.__get_live_status(uid_item)

                def callback():
                    func({
                        "name": self._uids[uid_item]['name'],
                        "uid": uid_item,
                        "status": self._uids[uid_item]['status']
                    }) if func else None

                if live_status == 1:
                    if self._uids[uid_item]["live_status"] == 0:
                        self._uids[uid_item]["live_status"] = 1
                        self._logger.info(f"开播提醒: {self._uids[uid_item]['name']} 开播了")
                        callback()
                else:
                    if self._uids[uid_item]["live_status"] == 1:
                        self._uids[uid_item]["live_status"] = 0
                        self._logger.info(f"下播提醒: {self._uids[uid_item]['name']} 下播了")
                        callback()

    def run(self, callback=None):
        """
            func 回调会传出一个dict
            dict = {
                "name": up主名称
                "uid": up主uid
                "status": 直播间情况, 1为直播中， 0为未直播
            }
        """
        self._logger.info(
            f"开播检测已挂载, 当前提醒的用户有: {' '.join(self._uids[uid_item]['name'] for uid_item in self._uids.keys())}")

        async def gather(func):
            await asyncio.gather(self.__pusher(func))

        asyncio.run(gather(callback))

    def add(self, *uids: int):
        for uid_item in uids:
            if uid_item not in self._uids:
                asyncio.run(self.__add(uid_item))

    async def __add(self, uid: int):
        user_info = await self.__get_user_info(uid)
        self._uids[uid] = \
            {
                "name": user_info["name"],
                "live_status": user_info["live_room"]["liveStatus"]
            }
        self._logger.info(f"新增 {user_info['name']}({uid}) 开播提醒")
        self._logger.info(f"现在 {user_info['name']}({uid}) 正在直播!") if \
            self._uids[uid]["live_status"] == 1 else None

    def remove(self, *uids: int):
        for uid_item in uids:
            if uid_item not in self._uids:
                self._logger.error(f"需要删除的uid: {uid_item}并不存在")
                continue
            self._logger.info(f"已删除 {self._uids[uid_item]['name']}({uid_item}) 的开播提醒")
            self._uids.pop(uid_item)
