"""
@Package   
@File      test_rabbit.py
@Version   V1.0
@Author    一云 <yi_yun200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from config.rabbitmq import RabbitConfig, RabbitManager, RabbitMQConnectionPool
import pytest

def test_config():
    # 初始化
    config = RabbitConfig()

    # 使用特定键
    config.use_key("account_pool")

    print("获取配置(转换成字典)：",config.get_config())

    # 获取基本信息
    print("获取交换机名：",config.get_exchange_name())
    print("获取不监控的队列列表：",config.get_not_control_queues())

    # 获取队列配置
    print("获取启动监控的队列配置：",config.get_start_monitoring_queues())
    print("获取启动监控的队列配置：",config.get_start_monitoring_queues("clear_note_hot_note"))

    # 获取所有队列名称
    all_queues = config.get_all_queue_names()
    print("所有队列名称：",all_queues)
    # 链式调用
    queue_info = (RabbitConfig()
                  .use_key("account_pool")
                  .get_start_monitoring_queues("clear_note_hot_note"))
    print("链式调用:",queue_info)

    print("通过交换机名和队列名获取是对应数据：",config.get_dict_exchange_and_queue("baiwan.pool","spider_account_pool"))

def test_manager():
    # 初始化
    manager = RabbitManager(RabbitConfig())

    print("创建任务字典:",manager.create_task("function_name", "arg1", "arg2",**{"a":1}))

    # 发送任务
    send_task = manager.create_task("function_name", "arg1", "arg2",**{"a":1})
    manager.send_task(send_task, "exchange_name", "queue_name")

    # 消费RabbitMQ中的任务
    manager.consume_tasks(exchange_name="exchange_name",
                         queue_name="queue_name")
    print("获取消费的数据:",manager.received_body)
    # 启动监控 一般不常用
    # manager.start_monitoring(exchange_name="exchange_name", queue_name={},not_control=[])
    # 清空并删除指定交换机下的所有队列
    # manager.clear_and_delete_queues("exchange_name", "queue_name", True, True)

    # 使用API操作
    print("获取所有绑定列表或者指定的绑定列表:",manager.get_exchange_bindings("exchange_name"))
    print("获取RabbitMQ中所有的队列信息或者指定:",manager.get_all_queues("exchange_name"))
    print("获取RabbitMQ中所有的交换机名称:",manager.get_all_exchanges("exchange_name"))
    print("获取当前RabbitMQ服务器上的连接列表:",manager.get_connections("host","user"))
    print("获取当前RabbitMQ服务器上的通道列表:",manager.get_channels("user","state"))
    print("声明队列并获取队列中的消息数量:",manager.get_queue_num("queye_name"))
    print("获取指定队列的消费者数量:",manager.get_queue_consumer_count("queye_name"))


    # 迁移RabbitMQ
    # manager.migrate_rabbitmq(RabbitConfig(),RabbitConfig(),["exchange_name"],["queue_name"],["exchange_name"],["queue_name"],True)
    # 关闭队列连接
    manager.close()
    # 上下文管理器的方法使用
    with RabbitManager(RabbitConfig()) as manager:
        manager.consume_tasks(exchange_name="exchange_name",
                             queue_name="queue_name")

def test_pool():
    # 创建连接池
    pool = RabbitMQConnectionPool(RabbitConfig(),pool_size=10)
    # 获取连接
    with pool.get_connection() as connection:
        # 使用连接
        connection.consume_tasks(exchange_name="exchange_name",
                                 queue_name="queue_name")
    print("获取连接池状态:",pool.get_pool_status())
    # 获取连接并立即返回
    connection, lock = pool.get_connection_nowait()
    # 使用连接
    connection.consume_tasks()
    # 释放一个RabbitMQ连接回连接池
    pool.release_connection(connection,lock)
    # 关闭所有连接
    pool.close_all()