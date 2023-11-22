import json
import os
import random

from src import Biliveir
from src.parse import DanmuMsg

biliveir = Biliveir(923833)


@biliveir.register(DanmuMsg.cmd, DanmuMsg.parser)
async def danmu(msg: DanmuMsg):
    print(msg)


@biliveir.register('UNREGISTERED')
async def unregistered(msg):
    print(msg)


@biliveir.register('ANY')
async def any_msg(msg: dict):
    dir_path = f"CmdJsonExample/{msg['cmd']}"
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    file_path = f"{dir_path}/{random.randint(0, 99)}.json"
    if os.path.exists(file_path):
        return
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(msg, f, indent=2, ensure_ascii=False)


biliveir.sync_run()
