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
from typing import Union

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

from app.types import RabbitMqConfig, RabbitMqStartMonitoring


class AppConfigSettings(BaseSettings):
    """应用配置
    
    属性:
        name (str): 应用名称，默认为"一云天"
        description (str): 应用描述，默认为"一云天私域"
        version (str): 应用版本号，默认为"1.0"
        docs_url (str | None): Swagger UI 文档的访问路径，设置为None时关闭SwaggerUI
        redoc_url (str): ReDoc 文档的访问路径，默认为"/redoc"
        openapi_url (Union[str | bool]): OpenAPI 文档的访问路径或布尔值，默认为"/openapi.json"
        prefix (str): 应用路由前缀，默认为'/'
        debug (bool): 是否启用调试模式，默认为True
        
        port (int): 应用监听端口，默认为8080
        host (str): 应用绑定主机地址，默认为"0.0.0.0 "
        reload (bool): 是否启用热重载，默认为True
        public_dir (dict): 静态文件目录配置字典，包含以下键：
            'STATIC': 基础静态资源路径
            'STATIC_MANAGE': 管理后台静态资源路径
            
        max_concurrency_count (int): 最大并发连接数，默认为12
        
    环境变量前缀: APP_
    """
    
    name: str = "一云天"
    description: str = "一云天私域"
    version: str = "1.0"
    # docs_url=None: 代表关闭SwaggerUi
    # redoc_url=None: 代表关闭redoc文档
    docs_url: str|None = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: Union[str | bool] = "/openapi.json"
    prefix: str = '/'
    debug:bool = True
    start_mq: bool = False

    port: int = 8080
    host: str = "0.0.0.0 "
    reload: bool = True
    public_dir: dict = {
        'STATIC': os.path.normpath(os.getcwd() + "/static"),
        'STATIC_MANAGE': os.path.normpath(os.getcwd() + "/static/manage"),
    }

    max_concurrency_count: int = 12  # 最大并发数

    class Config:
        env_prefix = "APP_"

class DBConfigSettings(BaseSettings):
    """
    数据库配置类，定义了与数据库连接所需的所有配置参数
    
    Attributes:
        host (str): 数据库服务器地址，默认为127.0.0.1
        port (int): 数据库服务端口，默认为8080
        user (str): 数据库用户名，默认为root
        password (str): 数据库密码，默认为root
        database (str): 默认连接的数据库名称，默认为database
        echo_sql (bool): 是否打印SQL日志信息，默认不打印
        pool_size (int): 连接池中的初始连接数，默认为5
        max_overflow (int): 连接池中允许的最大超出连接数，默认为10
        
    环境变量前缀: DB_
    """
    host: str = '127.0.0.1'
    port: int = 8080
    user: str = 'root'
    password: str = 'root'
    database: str = 'database'
    # 使用打印SQL日志信息
    echo_sql: bool = False
    # 连接池中的初始连接数，默认为 5
    pool_size: int = 5
    # 连接池中允许的最大超出连接数
    max_overflow: int = 10

    class Config:
        env_prefix = "DB_"

class RedisConfigSettings(BaseSettings):
    """
    Redis连接配置类，定义了与Redis服务器交互所需的所有配置参数
    
    Attributes:
        host (str): Redis服务器地址，默认为localhost
        port (int): Redis服务端口，默认为6379
        password (str): 认证密码，默认为空字符串
        db (int): 使用的数据库编号，默认为0
        decode_responses (bool): 是否自动解码响应数据，默认为True
        timeout (int): 命令执行超时时间(秒)，默认5秒
        connect_timeout (int): 连接建立超时时间(秒)，默认5秒
        max_connections (int): 最大连接池数量，默认10个
        retry_on_timeout (bool): 超时时是否自动重试，默认不重试
        health_check_interval (int): 健康检查间隔时间(秒)，默认30秒
        
    环境变量前缀: REDIS_
    """
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    decode_responses: bool = True
    timeout: int = 5
    connect_timeout: int = 5
    max_connections: int = 10
    retry_on_timeout: bool = False
    health_check_interval: int = 30

    class Config:
        """
        配置元类，定义环境变量加载规则
        """
        env_prefix = "REDIS_"

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

    RabbitMq: dict = {
        # "队列的 key": {
        #     "type": [],队列监控的类型  "start_monitoring","monitor_queue"
        #     "exchange_name": "",交换机名,
        #     "queue_start_monitoring": {
        #                 "title":"标题"
        #             "queue_name": "队列名",
        #             "queue_fun": "该队列对应的函数",
        #             "max_consumer":"同时启动多少个消费者"
        #         },
        #      "not_control": ["队列名1","队列名2"]  不监控的列表
        #     "queue_monitor_queue": [
        #                 {
        #                     "type":"类型" # count 根据数量监控, time 根据等待时间监控
        #                     "title":"标题"
        #                     "queue_name": "当前队列名",
        #                     "queue_fun": "队列函数",
        #                     "forward_queue_name": "转发的队列名",
        #                     "max_consumer": "同时启动多少个消费者",
        #                     "time_sleep" :"死循环的等待时间"
        #                 }
        #
        #             ]
        # },
        "account_pool": RabbitMqConfig(
            exchange_name="baiwan.pool",
            not_control=[],
            queue_start_monitoring={
                "spider_account_pool": RabbitMqStartMonitoring(
                    title="爬虫所用帐号池-不需要监控",
                    queue_name="spider_account_pool",
                    max_consumer=0,
                    is_create_task=False,
                )
            },
        ),
    }
    class Config:
        env_prefix = "RABBITMQ_"

class JWTConfigSettings(BaseSettings):
    """
    JWT配置类，定义了JSON Web Token相关的配置参数
    
    属性:
        enable (bool): 是否启用JWT鉴权功能，默认为False
        secret_key (str): 用于签名和验证JWT的密钥，默认为"12345789@98765431"
        algorithm (str): JWT签名算法类型，默认为"HS256"
        expired (int): 访问令牌过期时间(小时)，默认为1小时
        expired_refresh (int): 刷新令牌过期时间(小时)，默认为24小时
        iss (str): 签发者标识符，默认为"一一"
        
    环境变量前缀: JWT_
    """
    enable: bool = False
    secret_key: str = "12345789@98765431"
    algorithm: str = "HS256"
    expired: int = 1
    expired_refresh: int = 24
    iss: str = "一一"

    class Config:
        env_prefix = "JWT_"

# =================== 主配置容器 ===================
class Settings(BaseModel):
    app: AppConfigSettings
    db: DBConfigSettings
    redis:RedisConfigSettings
    RabbitMQ:MQConfigSettings
    jwt: JWTConfigSettings


# =================== 单例加载器 ===================
@lru_cache
def get_settings(dotenv_path: str = ".env") -> Settings:
    """
    获取全局配置对象，支持指定 .env 文件路径。

    :param dotenv_path: .env 文件路径，默认为当前目录下的 .env
    :return: 包含 app/db/jwt 等配置的 Settings 实例
    """
    load_dotenv(dotenv_path=dotenv_path)

    return Settings(
        app=AppConfigSettings(),
        db=DBConfigSettings(),
        redis=RedisConfigSettings(),
        RabbitMQ=MQConfigSettings(),
        jwt=JWTConfigSettings()
    )
# =================== 兼容旧写法（可选）===================
settings = get_settings()
appSettings = settings.app
dbSettings = settings.db
redisSettings = settings.redis
mqSettings = settings.RabbitMQ
jwtConfig = settings.jwt


__all__ = [
    'appSettings',
    'dbSettings',
    "redisSettings",
    "mqSettings",
    'jwtConfig',
]
