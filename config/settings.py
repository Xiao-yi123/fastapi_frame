"""
@Package   
@File      settings.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import os
import random
from typing import Union

from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv


class AppConfigSettings(BaseSettings):
    """应用配置"""
    name: str = "一云天"
    description: str = "一云天私域"
    version: str = "1.0"
    # docs_url=None: 代表关闭SwaggerUi
    # redoc_url=None: 代表关闭redoc文档
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: Union[str | bool] = "/openapi.json"
    debug: bool = False
    prefix: str = '/'
    start_mq:bool = False

    port: int = 8080
    host: str = "0.0.0.0 "
    env: str = "dev"
    reload: bool = True
    public_dir: dict = {
        'STATIC': os.path.normpath(os.getcwd() + "/static"),
        'STATIC_MANAGE': os.path.normpath(os.getcwd() + "/static/manage"),

    }

    max_concurrency_count: int = 12  # 最大并发数

    class Config:
        env_prefix = "APP_"


class DBConfigSettings(BaseSettings):
    """数据库配置"""
    host: str = '127.0.0.10'
    port: int = 8080
    user: str = 'root'
    password: str = 'root'
    database: str = 'database'
    # 使用打印SQL日志信息
    echo_sql: bool = False
    # 连接池中的初始连接数，默认为 5
    redis_connect_str: str = "localhost:6379"
    pool_size: int = 5
    # 连接池中允许的最大超出连接数
    max_overflow: int = 10

    class Config:
        env_prefix = "DB_"

class MQConfigSettings(BaseSettings):
    # 远程RabbitMQ服务器相关配置
    host: str = "127.0.0.1"  # 远程RabbitMQ服务器的IP地址
    port: int = 5672  # 默认端口
    user: str = "admin"  # 用户名和密码
    password: str = "admin"
    api_port: int = 15672
    virtual_host: str = "/"
    connection_attempts: int = 10  # 尝试连接的最大次数
    retry_delay: int = 5  # 每次重试之间的延迟时间（秒）
    socket_timeout: int = 12  # 套接字超时时间（秒）
    heartbeat: [int, None] = 0  # 在连接参数中设置心跳间隔，防止因长时间无活动导致的连接超时。 None，则禁用心跳。
    prefetch_count: int = 1  # 默认RabbitMQ 最大处理任务数量
    max_consumer: int = 5  # RabbitMQ 同时启动多少个消费者  用于监控的
    # 连接池中允许的最大超出连接数
    pool_max_overflow: int = 10
    blocked_connection_timeout:[int, None] = 10 # 设置阻塞连接超时时间

    # noinspection PyDataclass
    RabbitMq: dict = {
        # "key": QueueConfig(
        #     type=["start_monitoring"],
        #     exchange_name="baiwan.collection",
        #     not_control=[],
        #     queue_start_monitoring={
        #         "collection_comment": QueueStartMonitoring(),
        #     },
        #     queue_monitor_queue=[
        #         QueueMonitorQueue()
        #     ]
        # )
    }
    class Config:
        env_prefix = "RABBITMQ_"

class JWTConfigSettings(BaseSettings):
    """jwt配置"""
    enable: bool = False
    secret_key: str = "12345789@98765431"
    algorithm: str = "HS256"
    expired: int = 1
    expired_refresh: int = 24
    iss: str = "一一"
    no_check_uris: str = ""

    class Config:
        env_prefix = "JWT_"

class LogConfigSettings(BaseSettings):
    """日志配置"""
    enable: bool = False
    level: str = "DEBUG"
    log_path: str = os.path.normpath(os.getcwd() + "/logs")
    log_name: str = "app.logs"
    log_max_bytes: int = 1024 * 1024 * 10
    log_backup_count: int = 10
    sql_log_path: str = os.path.normpath(os.getcwd() + "/app/logs/sqlalchemy_logging.log")

    class Config:
        env_prefix = "LOG_"

@lru_cache
def getAppConfig() -> AppConfigSettings:
    # 加载 .env 文件，dotenv_path 变量默认是.env
    load_dotenv()
    # 实例化配置模型
    return AppConfigSettings()


@lru_cache
def getDbConfig() -> DBConfigSettings:
    # 加载 .env 文件，dotenv_path 变量默认是.env
    load_dotenv()
    # 实例化配置模型
    return DBConfigSettings()

@lru_cache
def getMQConfig() -> MQConfigSettings:
    # 加载 .env 文件，dotenv_path 变量默认是.env
    load_dotenv()
    # 实例化配置模型
    return MQConfigSettings()

@lru_cache
def getJWTConfig() -> JWTConfigSettings:
    # 加载 .env 文件，dotenv_path 变量默认是.env
    load_dotenv()
    # 实例化配置模型
    return JWTConfigSettings()


@lru_cache
def getLogConfig() -> LogConfigSettings:
    # 加载 .env 文件，dotenv_path 变量默认是.env
    load_dotenv()
    # 实例化配置模型
    return LogConfigSettings()


appSettings = getAppConfig()
dbSettings = getDbConfig()
mqSettings = getMQConfig()
jwtConfig = JWTConfigSettings()
logSettings = getLogConfig()

__all__ = [
    'appSettings',
    'dbSettings',
    "mqSettings",
    'jwtConfig',
    "logSettings",
]
