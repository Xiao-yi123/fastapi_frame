"""
@Package   
@File      __init__.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import os

from .log import *

rabbitmq_logger = logging_obj.setup_logger(
    'rabbitmq_logger', os.path.join(os.getcwd(), "app", "logs","other", "rabbitmq_logger.log")
)

