"""
@Package   
@File      rabbit_mq.py
@Version   V1.0
@Author    一云 <yi_yun200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from enum import Enum
from typing import List, Dict, Union
from dataclasses import dataclass
from pydantic import Field


class RabbitMqMonitorType(Enum):
    COUNT = "count"
    TIME = "time"


class RabbitMqConfigType(Enum):
    START = "start_monitoring"
    MONITOR = "monitor_queue"




@dataclass
class RabbitMqStartMonitoring:
    title: Union[str] = Field(
        default="",
        description="监控任务的标题"
    )  # 监控任务的标题

    queue_name: Union[str] = Field(
        default="",
        description="要监控的队列的名称"
    )  # 要监控的队列的名称

    queue_fun: Union[str] = Field(
        default="",
        description="与队列相关的函数名称"
    )  # 与队列相关的函数名称

    max_consumer: Union[int] = Field(
        default=0,
        description="队列的最大消费者数量"
    )  # 队列的最大消费者数量


@dataclass
class RabbitMqMonitorRabbitMq:
    type: Union[RabbitMqMonitorType] = Field(
        default=RabbitMqMonitorType.COUNT,
        description="指定队列监控的类型，默认为 COUNT，表示按消息数量监控；可选值包括 COUNT（按消息数量）和 TIME（按时间间隔）"
    )  # 指定队列监控的类型，默认为 COUNT，表示按消息数量监控；可选值包括 COUNT（按消息数量）和 TIME（按时间间隔）

    title: Union[str] = Field(
        default="",
        description="队列监控的标题"
    )  # 队列监控的标题

    queue_name: Union[str] = Field(
        default="",
        description="队列的名称"
    )  # 队列的名称

    queue_fun: Union[str] = Field(
        default="",
        description="与队列相关的函数名称"
    )  # 与队列相关的函数名称

    forward_queue_name: str = Field(
        default="",
        description="转发队列的名称"
    )  # 转发队列的名称

    max_consumer: Union[int] = Field(
        default=0,
        description="队列的最大消费者数量"
    )  # 队列的最大消费者数量

    time_sleep: Union[int] = Field(
        default=0,
        description="处理队列时的时间间隔，单位为秒"
    )


@dataclass
class RabbitMqConfig:
    type: Union[List[RabbitMqConfigType], None] = Field(
        default=None,
        description="队列配置的类型列表，可选值包括 START_MONITORING 和 MONITOR_QUEUE"
    )  # ["start_monitoring", "monitor_queue"]

    exchange_name: Union[str, None] = Field(
        default=None,
        description="交换机的名称"
    )  # 交换机的名称

    queue_start_monitoring: Union[Dict[str, RabbitMqStartMonitoring], None] = Field(
        default=None,
        description="启动监控的队列配置字典"
    )  # 启动监控的队列配置字典

    not_control: Union[List[str], None] = Field(
        default=None,
        description="不需要控制的队列名称列表"
    )  # 不需要控制的队列名称列表

    queue_monitor_queue: Union[List[RabbitMqMonitorRabbitMq], None] = Field(
        default=None,
        description="监控队列的配置列表"
    )  # 监控队列的配置列表


__all__ = ["RabbitMqMonitorType", "RabbitMqConfigType", "RabbitMqStartMonitoring", "RabbitMqMonitorRabbitMq", "RabbitMqConfig"]
