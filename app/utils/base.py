"""
@Package   
@File      platform.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import asyncio
import random
from datetime import datetime, timedelta

import aiohttp

from config.settings import appSettings


def is_within_last_seven_days(timestamp, day=7):
    """
    判断给定的时间戳是否在过去 day 天内。

    :param timestamp: 时间戳（整数）
    :return: 如果时间戳在过去7天内返回 True，否则返回 False
    """
    # 将时间戳转换为 datetime 对象
    dt_object = datetime.fromtimestamp(timestamp)

    # 获取当前时间
    now = datetime.now()

    # 计算7天前的时间
    seven_days_ago = now - timedelta(days=day)

    # 判断时间戳是否在过去7天内
    return seven_days_ago <= dt_object <= now


def generate_chinese(num=1):
    '''
    随机生成指定数量汉字
    '''
    random_chars = ''
    for i in range(num):
        # 生成第一个字节
        first = random.randint(0xB0, 0xF7)
        # 生成第二个字节
        last = random.randint(0xA1, 0xFE)

        # 组合一下
        s = f'{first:x}{last:x}'
        # 转换成汉字
        random_chars += bytes.fromhex(s).decode('gb2312')

    return random_chars

def convert_to_timestamp(date_string):
    """
    将给定的日期时间字符串转换为 Unix 时间戳。

    :param date_string: 日期时间字符串，格式为 "YYYY-MM-DDTHH:MM:SS"
    :return: Unix 时间戳
    """
    # 将字符串转换为 datetime 对象
    dt_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")

    # 将 datetime 对象转换为 Unix 时间戳
    timestamp1 = dt_object.timestamp()

    return timestamp1

async def async_execute_tasks(tasks, max_concurrency: int = None, timeout: int = None, return_exceptions: bool = True):
    """
    异步执行任务列表

    此函数用于异步执行一个任务列表，通过Semaphore控制并发执行的数量。
    Semaphore的使用确保了同时执行的任务数量不会超过预设的最大并发数量，
    这对于资源管理和错误控制是必要的。

    参数:
    - tasks: 一个包含异步任务的列表，每个任务将被独立执行。
    - max_concurrency: 最大并发数量，默认为None，表示使用全局配置。
    - timeout: 单个任务的超时时间（秒），默认为None，表示不设置超时。
    - return_exceptions: 布尔值，决定是否在任务抛出异常时将异常作为结果返回。

    返回:
    - 一个包含所有任务执行结果的列表。如果return_exceptions为True，
      则即使某些任务失败并抛出异常，也会将这些异常作为结果包含在内。
    """
    # 使用 Semaphore 控制并发数量
    semaphore = asyncio.Semaphore(max_concurrency if max_concurrency else appSettings.max_concurrency_count)

    async def run_task(task):
        async with semaphore:
            try:
                return await asyncio.wait_for(task, timeout=timeout)
            except asyncio.TimeoutError:
                return {"error": "Task timed out"}
            except Exception as e:
                return {"error": f"{e}"}

    # 直接使用 await 等待所有任务完成
    results = await asyncio.gather(*(run_task(task) for task in tasks), return_exceptions=return_exceptions)
    return results


async def get_public_ip():
    """
    异步获取当前设备的公网IP地址。

    该函数通过发送HTTP请求来获取设备的公网IP地址。如果请求成功且响应状态码为200，
    则返回获取到的IP地址。如果请求失败或响应状态码非200，则返回本地回环地址'127.0.0.1'。
    若在请求过程中遇到aiohttp库相关的错误，则返回具体的错误信息。

    Returns:
        str: 设备的公网IP地址或本地回环地址，或者请求错误信息。
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://ifconfig.me/ip') as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return "127.0.0.1"
    except aiohttp.ClientError as e:
        return f"请求错误: {e}"

__all__ = [
    "get_public_ip",
    "generate_chinese",
    'is_within_last_seven_days',
    'async_execute_tasks',
    "convert_to_timestamp"
]
