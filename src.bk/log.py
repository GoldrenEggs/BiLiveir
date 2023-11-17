import os
from datetime import datetime
from typing import Union

log_objs = {}


def get_log(path: str):
    file_stat_dev = os.stat(path)
    if file_stat_dev in log_objs:
        return log_objs[file_stat_dev]
    else:
        raise KeyError(f'路径 {path} 不存在Log对象')


class BaseLog:
    def __init__(self, file_path: str, date_format='%H:%M:%S', file_mode='a'):
        self._file_io = open(file_path, file_mode, encoding='utf-8')
        self.date_format = date_format
        file_stat_dev = os.stat(file_path).st_dev
        if file_stat_dev not in log_objs:
            log_objs[file_stat_dev] = self
        else:
            raise KeyError(f'以{file_path}为目标的Log对象已存在，如有需要可以使用get_log方法获取')

    @property
    def _date(self):
        return datetime.now().strftime(self.date_format)

    def save(self, text: str, end='\n'):
        self._file_io.write(text + end)
        self._file_io.flush()

    def debug(self, text):
        self.save(f'[{self._date}][DEBUG]{text}')

    def info(self, text):
        self.save(f'[{self._date}][INFO]{text}')

    def warn(self, text):
        self.save(f'[{self._date}][WARN]{text}')

    def error(self, text):
        self.save(f'[{self._date}][ERROR]{text}')

    def close(self):
        self._file_io.close()


class Log(BaseLog):
    COLOR_TABLE = {'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'purple': 35, 'aqua': 36, 'white': 37,
                   True: 33, False: 0}

    def __init__(self, file_path: str, color_print: bool = True, date_format: str = '%H:%M:%S', file_mode: str = 'a'):
        super().__init__(file_path, date_format, file_mode)
        self.color_print = color_print

    def debug(self, text):
        date = self._date
        self.save(f'[{date}][DEBUG]{text}')
        if self.color_print:
            print(f'\033[37m[{date}][DEBUG]{text}\033[0m')
        else:
            print(f'[{date}][DEBUG]{text}')

    def info(self, text, mark: Union[bool, str] = False):
        date = self._date
        self.save(f'[{date}][INFO]{text}')
        if self.color_print:
            print(f'\033[37m[{date}]\033[34m[INFO]\033[{self.COLOR_TABLE.get(mark, 0)}m{text}\033[0m')
        else:
            print(f'[{date}][INFO]{text}')

    def warn(self, text):
        date = self._date
        self.save(f'[{date}][WARN]{text}')
        if self.color_print:
            print(f'\033[37m[{date}]\033[1;33m[WARN]\033[0m{text}')
        else:
            print(f'[{date}][WARN]{text}')

    def error(self, text):
        date = self._date
        self.save(f'[{date}][ERROR]{text}')
        if self.color_print:
            print(f'\033[1;4;30;41m[{date}][ERROR]{text}\033[0m')
        else:
            print(f'[{date}][ERROR]{text}')


# noinspection PyMissingConstructor
class VoidLog(BaseLog):
    def __init__(self):
        self._file_io = None
        self.date_format = ''

    def debug(self, text: str):
        pass

    def info(self, text: str):
        pass

    def warn(self, text: str):
        pass

    def error(self, text: str):
        pass

    def close(self):
        pass


void_loger = VoidLog()
