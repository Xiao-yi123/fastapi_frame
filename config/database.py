"""
@Package   
@File      database.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""

from contextlib import contextmanager, asynccontextmanager

from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import dbSettings, redisSettings


@contextmanager
def getDatabaseSession(connect_str: None | str = None, autoCommitByExit: bool = True):
    # 数据库配置
    if connect_str is None:
        connect_str = f"{dbSettings.user}:{dbSettings.password}@{dbSettings.host}:{dbSettings.port}/{dbSettings.database}"
    SQLALCHEMY_DATABASE_URI_SYNC = (
        f"mysql+pymysql://{connect_str}"
    )
    # 创建同步引擎
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI_SYNC,
        echo=dbSettings.echo_sql,  # 是否打印SQL
        pool_size=dbSettings.pool_size,  # 连接池的大小，指定同时在连接池中保持的数据库连接数，默认:5
        max_overflow=dbSettings.max_overflow,  # 超出连接池大小的连接数，超过这个数量的连接将被丢弃,默认: 5
    )

    # 封装获取会话
    Session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)

    """使用上下文管理资源关闭"""
    _session = Session()
    try:
        yield _session
        # 退出时，是否自动提交
        if autoCommitByExit:
            _session.commit()
    except Exception as e:
        _session.rollback()
        raise e


# 定义异步上下文管理器
@asynccontextmanager
async def getDatabaseSessionAsync(connect_str: None | str = None, autoCommitByExit=True):
    if connect_str is None:
        connect_str = f"{dbSettings.user}:{dbSettings.password}@{dbSettings.host}:{dbSettings.port}/{dbSettings.database}"
    # 数据库配置
    SQLALCHEMY_DATABASE_URI_ASYNC = (
        f"mysql+aiomysql://{connect_str}"
    )
    # 创建异步引擎
    async_engine = create_async_engine(
        SQLALCHEMY_DATABASE_URI_ASYNC,
        echo=dbSettings.echo_sql,  # 是否打印SQL
        pool_size=dbSettings.pool_size,  # 连接池的大小
        max_overflow=dbSettings.max_overflow,  # 超出连接池大小的连接数
    )

    # 创建异步会话工厂
    AsyncSessionFactory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    """使用异步上下文管理器管理资源关闭"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # 退出时，是否自动提交
            if autoCommitByExit:
                await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    # 定义 Redis 连接池


@asynccontextmanager
async def getRedisConnectionAsync(connect_str: None | str = None):
    if connect_str is None:
        connect_str = f"{redisSettings.host}:{redisSettings.port}"
    redis_pool = ConnectionPool.from_url(
        url=f"redis://{connect_str}",
        decode_responses=redisSettings.decode_responses,  # 是否自动解码响应为字符串
        max_connections=redisSettings.max_connections,  # 最大连接数
        socket_timeout=redisSettings.timeout,  # 套接字读取超时时间（秒）
        socket_connect_timeout=redisSettings.connect_timeout,  # 连接建立超时时间（秒）
        retry_on_timeout=redisSettings.retry_on_timeout,  # 超时时是否重试
        health_check_interval=redisSettings.health_check_interval,  # 定期健康检查间隔
    )

    """使用异步上下文管理器管理 Redis 连接"""
    redis_client = Redis(connection_pool=redis_pool)
    try:
        yield redis_client
    finally:
        # 确保连接返回到连接池而不是关闭
        await redis_client.close()


__all__ = [
    "getDatabaseSession",
    'getDatabaseSessionAsync',
    "getRedisConnectionAsync"
]
