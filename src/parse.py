import abc
from typing import Self


class Message(abc.ABC):
    cmd: str

    # noinspection PyUnusedLocal
    @abc.abstractmethod
    def __init__(self, raw: dict):
        pass


class DanmuMsg(Message):
    cmd: str = 'DANMU_MSG'

    def __init__(self, raw: dict):
        data = raw['info']
        self.uid: int = data[2][0]
        self.name: str = data[2][1]
        self.message: str = data[1]
        self.is_emotion: bool = 'url' in data[0][13]
        self.emotion_pic: str = data[0][13]['url'] if self.is_emotion else ''

    def __str__(self):
        return f'{self.name}：{self.message}'

    @staticmethod
    async def parser(raw: dict) -> "Self":
        return DanmuMsg(raw)


if __name__ == '__main__':
    def adf(d: DanmuMsg):
        print(d.cmd)


    adf(DanmuMsg({}))
