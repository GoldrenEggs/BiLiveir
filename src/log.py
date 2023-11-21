import sys
from logging import Logger, StreamHandler, Formatter, LogRecord, NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL

__all__ = ['logger', ]

logger = Logger('Biliveir')

sh = StreamHandler(sys.stdout)
sh.setLevel(NOTSET)


class ColorfulFormatter(Formatter):
    FORMAT_MAP = {
        DEBUG: '\033[37m[{asctime}]\033[35m[DEBUG]\033[0m {msg}',
        INFO: '\033[37m[{asctime}]\033[34m[INFO]\033[0m {msg}',
        WARNING: '\033[37m[{asctime}]\033[1;33m[WARN]\033[0m {msg}',
        ERROR: '\033[37m[{asctime}]\033[31m[ERROR]\033[0m {msg}',
        CRITICAL: '\033[1;4;30;41m[{asctime}][CRITICAL] {msg}',
    }

    def format(self, record: LogRecord):
        return self.FORMAT_MAP.get(record.levelno, '[{asctime}][UNKNOWN] {msg}').format(
            asctime=self.formatTime(record, self.datefmt), msg=record.msg)


sh.setFormatter(ColorfulFormatter(datefmt='%H:%M:%S'))
logger.addHandler(sh)
