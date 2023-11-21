from src import Biliveir  # 导入Live类

live = Biliveir(114514)  # 创建一个Live对象，参数为房间号(roomid)


@live.danmu_msg  # 注册弹幕消息解析器
async def alpha(msg):  # 此处必须且只能包含一个必备参数
    print(msg)  # 打印msg对象，会调用data.__str__方法。


live.sync_run()  # 启动live

# Live(114514).run(False).heart_beat_reply(lambda data: print(data)),input()
