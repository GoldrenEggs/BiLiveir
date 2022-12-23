import os
import json
from random import randint

from src import Live, Log, messages

log = Log('log.txt')
live = Live(22889484, log)


@live.heart_beat_reply
async def heart_beat_reply(data: messages.HeartBeatReply):
    log.debug(repr(data))


@live.danmu_msg
async def danmu_msg(data: messages.DanmuMsg):
    log.info(data)




@live.super_chat_message
async def super_chat_message(data: messages.SuperChatMessage):
    print(data.uid, data.price)
    log.info(data)


@live.register('GUARD_BUY')
async def guard_buy(msg: dict):
    data = msg['data']
    log.info(f"{data['username']} 成为了 {data['gift_name']}")


@live.unregistered
async def unregistered(data: dict):
    cmd = data.get('cmd')
    log.debug(f'收到包: {cmd}')
    cmd_dir = f'CmdJsonExample/{cmd}'
    if not os.path.exists(cmd_dir):
        os.mkdir(cmd_dir)
    file_path = f'{cmd_dir}/{randint(0, 99)}.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


live.run(block=False)

live2 = Live(2668802)


@live2.all
async def all_cmd(data: dict):
    print(f'live2: {data}')


live2.run()
