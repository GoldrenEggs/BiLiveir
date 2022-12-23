BiLiveir - bilibili live message handler
===

最小应用示例
---

```python
from src import Live  # 导入Live类

live = Live(114514)  # 创建一个Live对象，参数为房间号(roomid)


@live.danmu_msg  # 注册弹幕消息解析器
async def alpha(msg):  # 此处必须且只能包含一个必备参数
    print(msg)  # 打印msg对象，会调用data.__str__方法。


live.run()  # 启动live
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

