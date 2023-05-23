BiLiveir - bilibili live message handler
===

概览
---

**一些术语**

|  术语   | 解释                                                                                                  |
|:-----:|-----------------------------------------------------------------------------------------------------|
| 消息处理器 | 一个由用户编写，使用了`Live`的方法装饰器的异步或普通函数，该函数形参中必须且只能包含一个必备参数，此参数类型可能为`字典`，也可能是一个属于`Message`的`类`，这取决于所使用的装饰器。 |
|  注册   | 将消息处理器注册到对应的执行列表中，当框架接收到对应的消息类型，则会将该消息内容作为参数传递给对应的消息处理器。                                            |

本工具以**尽可能不干涉用户的任何行为**为核心思想进行设计，你可以很轻松的将其集成到其他项目中。  
使用此消息流抓取工具时，您可以选择使用默认的消息处理方法，
该方法会提取一些关键的数据，传递给消息处理器，也可以参考[CmdJsonExample](CmdJsonExample "从管人那爬的数据")
中的消息示例文件，自定义处理原始数据。  
此外，本工具还提供了一种在windows平台或许比较好用的日志工具`Log`，你可以把该工具的实例传递给`Live`，以记录执行日志。
个人比较推荐在记录弹幕或其他信息时使用`Log`工具。  
顺带一提，您可以在任何流程任意时间注册消息处理器，功能将会如期执行，虽然目前还没有注销消息处理器的方法。

最小应用示例
---

```python
from src import Live  # 导入Live类

live = Live(114514)  # 创建一个Live对象，参数为房间号(roomid)


@live.danmu_msg  # 注册弹幕消息解析器
async def alpha(msg):  # 此处必须且只能包含一个必备参数
    print(msg)  # 打印msg对象，会调用msg.__str__方法。


live.run()  # 启动live
```

~~真正的最小应用示例：~~  
~~`Live(114514).run(False).danmu_msg(lambda data: print(data)), input()`~~

使用方法
---
详见 [start.py](start.py)

文件结构：

```
Biliveir
│
├─src - 代码
│  ├─crawler.py - 直播连接工具与消息推送处理器
│  ├─live_pusher.py - 开播推送及提醒相关，无用(不是我写的)
│  ├─log.py - 日志记录工具
│  └─message.py - 消息类及原始消息解析方法（待补充）
│
├─CmdJsonExample - 原始消息结构示例
│  ├─DANMU_MSG - 弹幕消息示例
│  │  ├─0.json - 第一个示例文件
│  │  └─...
│  │
│  ├─GUARD_BUY - 大航海消息示例
│  └─...
│
├─start.py - 整体使用示例
├─minimize.py - 最小应用示例
├─requirement.txt - 必备第三方模块
└─LICENSE - 开源协议
```

类 - Object
---

### `Live`

#### `Live.__init__(self, room_id: int, logger: Log = void_loger)`

`Live`的实例初始化函数，`room_id`为对应直播间的房间号，`logger`则为`src.log.Log`对象，若实例化一个`Log`
对象并传入，则会记录一些程序执行信息至log中，详情请查看章节：***Log***。

- *`logger`的默认参数`void_logger`不会执行任何操作。*

<br>

#### `Live.run(self, block=True)`

执行该函数后启动本程序，`block`值为`True`时，程序将发生阻塞，直到在控制台输入`q`、`quit`或`exit`后停止；
当值为`False`时，不产生阻塞，如果未执行其他任务，则程序自动结束。

- 您可以在任何时间注册协程至目标`cmd`，无论`Live.run`是否执行，程序都会正常运行。
- 您当然可以直接以函数的形式使用装饰器注册目标协程，关于装饰器如有需要请查阅：
  [PEP 318: 函数和方法的装饰器](https://docs.python.org/zh-cn/3.10/whatsnew/2.4.html#pep-318-decorators-for-functions-and-methods)
  [PythonDecoratorLibrary](https://wiki.python.org/moin/PythonDecoratorLibrary)  
  例：`live.register('DANMU_MSG')(target_func)`

<br>

#### `Live.register(self, cmd: str = '')`

执行该函数后返回一个装饰器，该装饰器会注册目标协程至`cmd`，当程序接收到对应`cmd`
的消息时会传入一个包含消息内容的字典对象至该协程并启动。

```python
@live.register('DANMU_MSG')
async def danmu_msg(msg: dict):
    pass
```

- *该装饰器不会对函数进行任何装饰，函数会原封不动的返回，若有意愿，您可以继续随意调用你的函数而不受影响。*
- *`cmd`种类及字典结构可以参考`CmdJsonExample`文件夹中的内容。*

<br>

#### `Live.unregistered(self, func: Callable[[dict], Any])`

装饰器，注册目标协程至`UNREGISTERED`，在执行过程中所有未被注册的`cmd`都会传入目标协程并启动该协程。

```python
@live.unregistered
async def unregistered(msg: dict):
    pass
```

- *该装饰器同样不会对原协程产生任何影响。*

<br>

#### `Live.all(self, func: Callable[[dict], Any])`

装饰器，注册目标协程至所有`cmd`。

```python
@live.all
async def anything(msg: dict):
    pass
```

- *注意，使用该装饰器将导致`Live.unregistered`失效。*
- *该装饰器同样不会对原协程产生任何影响。*

<br>

#### `Live.danmu_msg(self, func: Callable[[DanmuMsg], Any])`

装饰器，注册目标协程至`DANMU_MSG`，该装饰器会将处理过的消息解析并封装成`src.messages`中的对象传递给目标协程。

```python
@live.damu_msg
async def danmu_msg(data: messages.DanmuMsg):
    pass
```

- *传递给函数中的对象详见章节：**Message类**。*
- *其他消息解析装饰器同理，不做展示。*

### `Log(BaseLog)`

#### `Log.debug`

Message类 - Message Object
---

