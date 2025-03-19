import sys

from loguru import logger


class Logging:

    def __init__(self):
        self.loggers = {}  # 存储不同的 logger 实例
        # logger.remove()

    def setup_logger(self, name, sink=sys.stdout, level="DEBUG", rotation="2MB",retention="7 days", **keyword):
        if name not in self.loggers:
            # 创建一个新的绑定的 logger 实例
            new_logger = logger.bind(name=name)
            new_logger.add(
                sink=sink,
                level=level,
                format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {file} | {line} | {message}',
                filter=lambda record: record["extra"].get("name") == name,
                rotation=rotation,
                retention=retention,
                **keyword
            )
            self.loggers[name] = new_logger
        return self.loggers[name]


logging_obj = Logging()

__all__ = ['Logging', 'logging_obj']
