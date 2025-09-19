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
from typing import List, Dict, Union, Optional
from dataclasses import dataclass, field
from pydantic import Field, field_validator, BaseModel, model_validator





# @dataclass
class RabbitMqStartMonitoring(BaseModel):
    """
    启动监控任务的数据模型。
    """
    title: str = Field(description="监控任务的标题")
    queue_name: str = Field(description="要监控的队列的名称")
    queue_fun: str = Field(default="", description="与队列相关的函数名称")
    max_consumer: int = Field(default=0,ge=0, description="队列的最大消费者数量")
    is_create_task: bool = Field(
        default=True,
        description="是否创建任务"
    )

    @model_validator(mode='after')
    def validate_queue_fun_required(self) -> 'RabbitMqStartMonitoring':
        # 当 max_consumer 大于 0 且 is_create_task 为 True 时，queue_fun 不能为空
        if self.max_consumer > 0 and self.is_create_task and not self.queue_fun.strip():
            raise ValueError('当 max_consumer > 0 且 is_create_task 为 True 时，queue_fun 不能为空')
        return self
    @model_validator(mode='after')
    def validate_is_create_task(self) -> 'RabbitMqStartMonitoring':
        if self.is_create_task and self.max_consumer == 0:
            self.is_create_task =  False
        return self

    class Config:
        validate_assignment = True

@dataclass
class RabbitMqConfig:
    """
    队列整体配置的数据模型。
    """
    exchange_name: Optional[str] = Field(
        default=None,
        description="交换机的名称"
    )
    queue_start_monitoring: Optional[Dict[str, RabbitMqStartMonitoring]] = Field(
        default=None,
        description="启动监控的队列配置字典"
    )
    not_control: Optional[List[str]] = Field(
        default=None,
        description="不需要控制的队列名称列表"
    )


__all__ = [
    "RabbitMqStartMonitoring",
    "RabbitMqConfig"
]