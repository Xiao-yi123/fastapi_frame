"""
@Package   
@File      RedisCURD.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import random

from config.database import getRedisConnectionAsync


class RedisCURD:
    """Redis CRUD 操作类"""

    def __init__(self, connect_str: None|str = None):
        """
        初始化方法，设置模型类为None。
        """
        self.connect_str = connect_str
        
    async def create(self, key, value,expire=None):
        """创建键值对 并可选地设置过期时间（秒）"""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string.")
        async with getRedisConnectionAsync(self.connect_str) as redis_conn:
            try:
                await redis_conn.set(key, value)
                # 如果设置了过期时间，则应用之
                if expire is not None and expire > 0:
                    await redis_conn.expire(key, time=expire)  # 设置过期时间为 expire 秒

                return True
            except Exception as e:
                print(f"Error setting key-value: {e}")
                return False

    async def read(self, key):
        """读取键值对"""
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                return await redis_conn.get(key)
            except Exception as e:
                print(f"Error getting key-value: {e}")
                return None
    async def update(self, key, value,expire=None):
        """更新键值对"""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string.")
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                await redis_conn.set(key, value)
                if expire is not None and expire > 0:
                    await redis_conn.expire(key, time=expire)  # 设置过期时间为 expire 秒
                return True
            except Exception as e:
                print(f"Error updating key-value: {e}")
                return False

    async def delete(self, key):
        """删除键值对"""
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                return await redis_conn.delete(key)
            except Exception as e:
                print(f"Error deleting key: {e}")
                return False

    async def get_all(self, pattern='*'):
        """获取所有键值对或以特定模式开头的键值对"""
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            cursor = '0'
            keys = []
            while cursor != 0:
                cursor, data = await redis_conn.scan(cursor=cursor, match=pattern, count=100)
                keys.extend(data)
            # 批量获取值
            values = await redis_conn.mget(keys)
            results = dict(zip(keys, values))
            return results

    async def get_keys(self, pattern="*"):
        """
        异步获取匹配指定模式的Redis键。

        该方法通过连接到Redis服务器，根据传入的模式匹配参数获取相应的键。
        默认匹配所有键（"*"）。

        参数:
        pattern (str): 匹配键的模式。默认为 "*"，匹配所有键。

        返回:
        list: 匹配的键列表。如果发生错误，则返回空字典。

        注意:
        使用Redis的keys命令可能会导致Redis服务器短时间的阻塞，特别是在大数据集环境下。
        因此，在生产环境中使用此方法时需谨慎。
        """
        # 异步获取Redis连接
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                # 使用Redis的keys命令来获取所有匹配pattern的键
                # 注意：keys命令在大数据集中可能会阻塞Redis服务器，应谨慎使用
                keys = await redis_conn.keys(pattern)
                return keys
            except Exception as e:
                # 错误处理：打印模糊搜索期间的错误信息
                print(f"Error during fuzzy search: {e}")
                return {}

    async def delete_keys_with_pattern(self, pattern):
        """根据通配符模式删除所有匹配的键"""
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                # 获取所有匹配模式的键
                matching_keys = await redis_conn.keys(pattern)

                if not matching_keys:
                    return f"No keys found for pattern: {pattern}"

                # 批量删除所有匹配的键
                results = await redis_conn.delete(*matching_keys)

                return f"Deleted {results} keys matching pattern: {pattern}"
            except Exception as e:
                print(f"Error deleting keys with pattern: {e}")
                return False

    async def get_random_value(self, pattern="*"):
        """
        随机获取匹配指定模式的Redis键的值。

        参数:
        pattern (str): 匹配键的模式。默认为 "proxy_*"。

        返回:
        str: 随机键的值。如果发生错误或没有匹配的键，则返回 None。
        """
        async with getRedisConnectionAsync(connect_str=self.connect_str) as redis_conn:
            try:
                # 获取所有匹配模式的键
                keys = await redis_conn.keys(pattern)

                if not keys:
                    print(f"No keys found for pattern: {pattern}")
                    return None

                # 随机选择一个键
                random_key = random.choice(keys)

                # 获取该键的值
                value = await redis_conn.get(random_key)

                return value
            except Exception as e:
                print(f"Error getting random proxy value: {e}")
                return None


__all__ = ['RedisCURD']

async def main():
    redis_curd = RedisCURD()
    s = await redis_curd.get_random_value("proxy_fsd*")
    print("fsd",s)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())