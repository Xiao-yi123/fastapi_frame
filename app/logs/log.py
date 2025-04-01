import sys

from loguru import logger


class Logging:

    def __init__(self):
        self.loggers = {}  # 存储不同的 logger 实例

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

    @staticmethod
    def logobj_to_path(logger_obj,keyword: str):
        """
        根据关键字转换日志对象为路径。

        该函数遍历日志对象的所有处理程序，寻找其 sink 属性中包含指定关键字的处理程序。
        如果找到，返回该处理程序的 sink 属性（假设它是一个路径）；
        如果没有找到，返回 False。

        参数:
        keyword (str): 用于匹配的关键词。

        返回:
        str 或 bool: 匹配到的路径字符串，如果没有匹配到，则返回 False。
        """
        # 获取 logger_obj 的所有处理程序
        handlers = logger_obj._core.handlers

        # 提取所有具有字符串类型 sink 属性的处理程序
        sinks = [
            handler._sink._file_path  # handler[2] 是 sink 属性
            for handler in handlers.values()
            if hasattr(handler._sink, "_file_path")
        ]

        # 遍历并尝试匹配关键字
        for sink in sinks:
            if keyword in sink:
                # 如果找到匹配的关键字，返回对应的 sink
                return sink

        # 如果没有找到匹配项，返回 False
        return False


logging_obj = Logging()

__all__ = ['Logging', 'logging_obj']
