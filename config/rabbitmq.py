import asyncio
import contextlib
import json
import random
import threading
import time
import pika
import requests

from app.logs import rabbitmq_logger
from config.settings import mqSettings

# 不能删
from app.controllers import *


class RabbitManager:
    def __init__(self, rabbit_config):

        self._rabbitmq_host = rabbit_config.get('host', "127.0.0.1")
        self._rabbitmq_port = rabbit_config.get('port', 5672)
        self._rabbitmq_user = rabbit_config.get('user', None)
        self._rabbitmq_password = rabbit_config.get('password', None)
        self._rabbitmq_api_port = rabbit_config.get('api_port', 15672)
        self._virtual_host = rabbit_config.get('virtual_host', "/")  # 指定虚拟主机
        self._max_rebbitmq_prefetch_count = rabbit_config.get('max_rebbitmq_prefetch_count', 3)
        # 构造RabbitMQ API的URL
        self._rabbitmq_api_url = f"http://{self._rabbitmq_host}:{self._rabbitmq_api_port}/api/"
        # 使用RabbitMQ的认证信息
        self._auth = (self._rabbitmq_user, self._rabbitmq_password)
        # RabbitMQ 同时启动多少个消费者
        self._max_consumer = rabbit_config.get("max_consumer", 5)
        self._heartbeat = rabbit_config.get("heartbeat")  # 在连接参数中设置心跳间隔，防止因长时间无活动导致的连接超时。
        self._heartbeat = int(self._heartbeat) if self._heartbeat else None
        # 收到的正文
        self.received_body = None
        self._blocked_connection_timeout = rabbit_config.get('blocked_connection_timeout', None) # 设置阻塞连接超时时间
        self.connection_attempts = rabbit_config.get('connection_attempts', 10)  # 尝试连接的最大次数
        self.retry_delay = rabbit_config.get('retry_delay', 5)  # 每次重试之间的延迟时间（秒）
        self.socket_timeout = rabbit_config.get('socket_timeout', 10)  # 套接字超时时间（秒）

        # 建立与RabbitMQ的连接并获取信道
        self.connection, self.channel = self.connect_to_rabbitmq()
        # 是否初始化 exchange_and_queue
        self._is_init_exchange_and_queue: bool = False

    def _init_exchange_and_queue(self, exchange_name, queue_name):
        # 声明交换机，类型为direct
        self.channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)

        # 声明队列，使其持久化
        self.channel.queue_declare(queue=queue_name, durable=True)

        # 将队列与交换机绑定
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # 设置每个消费者同时最多处理的消息数量
        self.channel.basic_qos(prefetch_count=self._max_rebbitmq_prefetch_count)

        self._is_init_exchange_and_queue = True
    def close(self):
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.channel.close()
        self.connection.close()

    def create_task(self, function_name, *args, **kwargs):
        # 创建任务
        return {
            "function_name": function_name,
            "args": args,
            **kwargs
        }

    def connect_to_rabbitmq(self, max_retries=5, retry_delay=5):
        """
        连接到RabbitMQ服务器。

        参数:
        - max_retries (int): 最大重试次数，默认为5次。
        - retry_delay (int): 每次重试之间的延迟时间，默认为5秒。

        返回:
        - connection: 建立的RabbitMQ连接。
        - channel: RabbitMQ通道。

        异常:
        - RuntimeError: 在多次重试后未能连接到RabbitMQ。
        """
        # 连接到RabbitMQ
        rabbitmq_params = pika.ConnectionParameters(
            host=self._rabbitmq_host,  # 远程RabbitMQ服务器的IP地址
            port=self._rabbitmq_port,  # 默认端口
            virtual_host=self._virtual_host,  # 指定虚拟主机
            credentials=pika.PlainCredentials(self._rabbitmq_user, self._rabbitmq_password),  # 用户名和密码
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
            socket_timeout=self.socket_timeout,
            heartbeat=self._heartbeat,
            blocked_connection_timeout=self._blocked_connection_timeout
        )
        """重试连接RabbitMQ"""
        for _ in range(max_retries):
            try:
                connection = pika.BlockingConnection(rabbitmq_params)
                channel = connection.channel()
                return connection, channel
            except pika.exceptions.AMQPConnectionError as e:
                rabbitmq_logger.error(f"Failed to connect to RabbitMQ, retrying in {retry_delay} seconds...")
                rabbitmq_logger.error(f"error: {e}")
                time.sleep(retry_delay)

        raise RuntimeError("Failed to connect to RabbitMQ after multiple retries.")

    def send_task(self, task, exchange_name='', queue_name=''):
        """
        发送任务到指定的交换机和队列。

        本函数负责将任务消息发送到RabbitMQ的指定交换机和队列。它首先建立与RabbitMQ的连接，
        然后声明交换机和队列，最后发送任务消息，并确保消息和队列都是持久化的。

        参数:
        - task: 任务字典，包含要执行的任务信息。
        - exchange_name: 交换机名称。默认为空字符串，表示使用默认交换机。
        - queue_name: 队列名称。默认为空字符串。

        返回值:
        无返回值，但会记录发送任务的日志信息。
        """
        # 建立与RabbitMQ的连接并获取信道
        # connection, channel = self.connect_to_rabbitmq()
        # 声明交换机，使用direct类型
        self.channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)

        # 声明队列，并设置为持久化队列
        self.channel.queue_declare(queue=queue_name, durable=True)

        # 将队列绑定到交换机
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # 发送消息到交换机
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=queue_name,
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2)  # 使消息持久化
        )
        # 记录发送任务的日志信息
        if isinstance(task, dict) and task.get("function_name"):
            rabbitmq_logger.debug(
                f" [x] Sent exchange_name={exchange_name},queue={queue_name},function_name={task.get("function_name")}")
            # # 关闭RabbitMQ连接
            # self.channel.close()

    def process_task(self, ch, method, properties, body):
        """
        处理来自队列的任务。

        该方法接收一个消息并根据消息内容动态执行相应的函数。处理完任务后，向队列发送确认信号。

        参数:
        - self: 实例对象
        - ch: 通道
        - method: 方法框，包含方法的属性
        - properties: 消息的属性
        - body: 消息体，包含任务的JSON数据

        返回值:
        None
        """
        # 解析任务JSON数据
        task = json.loads(body)
        self.received_body = task
        # 确认处理完消息，向队列发送确认信号
        # ch.basic_ack(delivery_tag=method.delivery_tag)
        # 记录接收到的任务信息
        if isinstance(task, dict) and task.get("function_name"):
            rabbitmq_logger.debug(
                f" [x] Received exchange={method.exchange}, queue={method.routing_key},function_nema={task.get("function_name")}")
        try:
            self.run_def(task, ch)
        except pika.exceptions.StreamLostError as e:
            rabbitmq_logger.error(f"ChannelWrongStateError: {e},boby:{body}")
        except requests.exceptions.ConnectionError as e:
            rabbitmq_logger.error(f"Connection error: {e}, body:{body}")

        except Exception as e:
            # 如果发生异常，则记录错误信息
            rabbitmq_logger.error(f"Error processing task: {type(e).__name__} - {e},boby:{body}")
        finally:
            # 确认处理完消息，向队列发送确认信号
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def run_def(self, task, ch=None):
        """
        执行定义的函数。

        从任务字典中提取函数名、位置参数和关键字参数，并尝试执行该函数。
        如果函数名未定义或执行过程中出现异常，则根据情况返回任务字典或停止消费。

        参数:
        - task: 包含函数名、位置参数和关键字参数的任务字典。
        - ch: 消息队列通道对象，用于停止消费操作。

        返回:
        无返回值。根据执行情况更新 self.received_body 或停止消费。
        """
        try:
            # 尝试从任务对象中获取函数名、位置参数和关键字参数
            function_name = task.get("function_name", None)
            args = task.get("args", [])
            kwargs = task.get("kwargs", {})
        except:
            # 如果提取过程中出现异常，则重置函数名和参数
            function_name = None
            args = []
            kwargs = {}

        # 动态获取函数对象并执行
        func = globals().get(function_name)

        # 检查是否指定了函数名称
        if function_name is None:
            # 如果没有指定函数名称，则直接返回原始的任务字典
            self.received_body = task
            if ch:
                # 停止消费
                ch.stop_consuming()
        elif func:
            # 如果找到了对应的函数
            if asyncio.iscoroutinefunction(func):
                # 如果函数是异步的，则创建新的事件循环并运行
                # loop = asyncio.new_event_loop()
                # asyncio.set_event_loop(loop)
                # loop.run_until_complete(func(*args, **kwargs))
                # loop.close()
                # 如果函数是异步的，则在当前事件循环中运行
                asyncio.run(func(*args, **kwargs))
            else:
                # 如果函数是同步的，则直接调用
                func(*args, **kwargs)

            # 任务完成后记录信息
        else:
            # 如果找不到对应的函数则记录错误信息
            rabbitmq_logger.debug(f"Function '{function_name}' not found")

    def consume_tasks(self, exchange_name="", queue_name=''):
        """
        消费RabbitMQ中的任务。

        本函数旨在建立与RabbitMQ的连接，并准备必要的声明与绑定操作，以便可以消费队列中的任务。
        它主要执行以下操作：
        - 与RabbitMQ建立连接。
        - 声明（或创建）一个交换机，并将其类型设置为'direct'。
        - 声明（或创建）一个持久化队列。
        - 将队列与交换机绑定。
        - 设置每个消费者同时最多处理的消息数量。
        - 开始消费队列中的消息，并指定消息处理回调函数为`process_task`。

        参数:
            exchange_name (str): RabbitMQ中交换机的名称。默认为空字符串。
            queue_name (str): 队列的名称。默认为空字符串。

        注意:
        - 参数`exchange_name`和`queue_name`通常在创建队列或交换机时指定。
        - 这个函数假设RabbitMQ服务已经启动，并且可以通过`self.connect_to_rabbitmq()`方法进行连接。
        """
        try:
            if not self._is_init_exchange_and_queue:
                self._init_exchange_and_queue(exchange_name=exchange_name, queue_name=queue_name)
            # 开始消费队列中的消息
            self.channel.basic_consume(queue=queue_name, on_message_callback=self.process_task)

            # 开始监听并消费消息
            self.channel.start_consuming()
        except Exception as e:
            self._is_init_exchange_and_queue = False
            rabbitmq_logger.error(f"Error while consuming tasks: {e}")

    def start_monitoring(self, exchange_name, queue_name=None, not_control=[]):
        """
        开始监控指定的交换机下的队列。

        如果没有指定队列名，则监控该交换机下的所有队列，通过获取交换机的所有绑定信息，
        并为每个绑定启动一个消费线程。如果指定了队列名，则只监控该交换机下的指定队列，
        并启动一个消费线程来处理。

        参数:
            exchange_name (str): 要监控的交换机的名称。
            queue_name (str, 可选): 要监控的特定队列的名称。如果没有提供，则监控所有队列。
            not_control(list): 不监控的列表

        返回:
            无
        """

        from config.rabbitmq import rabbit_config as new_rabbit_config

        for queue in queue_name.values():
            if queue.get("queue_name") in not_control:
                continue
            for n in range(queue.get("max_consumer", self._max_consumer)):
                threading_name = f"{exchange_name}-{queue['queue_name']}-{n}"
                rabbit = RabbitManager(new_rabbit_config)
                consumer_thread = threading.Thread(target=rabbit.consume_tasks, name=threading_name, daemon=True,
                                                   args=(exchange_name, queue.get("queue_name")))
                consumer_thread.start()

    def monitor_queue_of_monitor(self, exchange_name: str, queue_info: dict, rabbit):
        """
        监控单个消息队列。

        此函数在一个无限循环中检查指定队列的状态，并在队列长度大于零时消费队列中的任务。

        参数:
        - exchange_name: str, 交换机名称。
        - queue_name: str, 需要监控的队列名称。
        - queue_fun: str, 当队列中有任务时需要执行的函数名称。
        """
        while True:

            # 根据队列的类型执行相应的逻辑
            if queue_info.get("type") == "count":
                result = rabbit.channel.queue_declare(queue=queue_info.get("queue_name"), durable=True)

                if not result:
                    # 获取所有队列信息，检查指定的队列是否存在
                    rabbit.channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)
                    continue
                # 检查队列长度，如果大于零，则消费任务
                if result.method.message_count > 0:
                    rabbit.consume_tasks(exchange_name, queue_info.get("queue_name"))
                    # 创建并发送任务
                    task = rabbit.create_task(queue_info.get("queue_fun"), kwargs=rabbit.received_body)
                    rabbit.send_task(task, exchange_name=exchange_name, queue_name=queue_info.get("forward_queue_name"))
                    continue
            elif queue_info.get("type") == "time":
                # 根据时间消费任务 执行函数 目前只能执行不带参数的函数
                task = rabbit.create_task(queue_info.get("queue_fun"))
                rabbit.run_def(task)
            else:
                break

    def monitor_queue(self, exchange_name: str, queue_info: list = None):
        """
        监控消息队列。

        此函数用于监控一个或多个消息队列的状态，并在满足特定条件时消费队列中的任务。

        参数:
        - exchange_name: str, 交换机名称，用于路由消息。
        - queue_info: list, 包含队列信息的列表，每个元素是一个字典，包含队列名称和处理函数。

        此函数内部定义了一个名为 monitor 的辅助函数，用于具体监控和处理单个队列。
        """
        from config.rabbitmq import rabbit_config as new_rabbit_config
        # 为每个队列信息启动一个线程来监控队列
        for i in queue_info:
            for n in range(i.get("max_consumer", self._max_consumer)):
                rabbit = RabbitManager(new_rabbit_config)
                threading_name = f"{exchange_name}-{i['queue_name']}-{n}"
                consumer_thread = threading.Thread(target=self.monitor_queue_of_monitor, name=threading_name,
                                                   daemon=True, args=(exchange_name, i, rabbit))
                consumer_thread.start()

    def clear_and_delete_queues(self, exchange_name, queue_name=None, is_delete_exchange=False,is_delete_queue=False):
        """
        清空并删除指定交换机下的所有队列。

        参数:
        - exchange_name (str): 交换机名称。
        - queue_name (str): 队列名称
        - is_delete_exchange (bool): 是否删除队列
        - is_delete_queue (bool): 是否删除队列

        注意:
        - 此函数假定已经有一个有效的channel连接。
        """
        # # 建立与RabbitMQ的连接并获取通道
        # connection, channel = self.connect_to_rabbitmq()
        # 获取交换机下的所有队列
        queue_names = [queue['routing_key'] for queue in self.get_exchange_bindings(exchange_name)]
        if queue_name:
            if queue_name in queue_names:
                # 清空并根据is_delete参数决定是否删除指定队列
                self.clear_queue(queue_name, is_delete=is_delete_queue)
        else:
            for queue_name in queue_names:
                # 对queue_names中的每一个队列执行清空操作，并根据is_delete参数决定是否删除队列
                self.clear_queue(queue_name, is_delete=is_delete_queue)

        # 是否删除该交换机
        if is_delete_exchange:
            self.channel.exchange_delete(exchange_name)

    def clear_queue(self, queue_name, is_delete=False):
        """
        清空指定的RabbitMQ队列。

        参数:
        - channel: 已经建立好的RabbitMQ通道。
        - queue_name (str): 需要清空的队列名称。
        - is_delete (bool): 是否删除
        注意:
        - 此函数假定已经有一个有效的channel连接。
        """
        # # 建立与RabbitMQ的连接并获取通道
        # connection, channel = self.connect_to_rabbitmq()
        # 首先确认队列存在
        self.channel.queue_declare(queue=queue_name, durable=True)

        while True:
            # 然后清空队列
            method_frame, header_frame, body = self.channel.basic_get(queue=queue_name, auto_ack=True)
            if method_frame is None:
                break
        if is_delete:
            # 删除队列
            self.channel.queue_delete(queue=queue_name)

    def get_exchange_bindings(self, exchange_name=None):
        """
        获取所有绑定列表或者指定的绑定列表

        参数:
        exchange_name (str): 交换机名称。如果不指定，则返回所有交换机下的队列；否则返回指定交换机下的队列。

        返回:
        list: 绑定到指定交换机的队列列表。如果未找到任何队列或请求失败，则返回空列表。
        """
        # 构造RabbitMQ API的URL
        rabbitmq_api_url = f"{self._rabbitmq_api_url}bindings?source="
        # 获取交换机下的所有队列
        response = requests.request("GET", rabbitmq_api_url, auth=self._auth)
        # response.raise_for_status()
        if response.status_code == 200:
            bindings = response.json()
            if exchange_name:
                # 过滤出属于指定交换机的队列
                return [binding for binding in bindings if binding["source"] == exchange_name]
            else:
                return bindings
        else:
            # 记录请求失败的错误日志
            rabbitmq_logger.error(
                f"Failed to fetch bindings for exchange {exchange_name}: {response.status_code} - {response.text}")
            return []

    def get_all_queues(self, queue_name=None):
        """
        获取RabbitMQ中所有的队列信息或者指定。
        result['backing_queue_status']['len'] == Ready
        result['backing_queue_status']['num_pending_acks'] == Unacked
        result['backing_queue_status']['num_pending_acks'] + result['backing_queue_status']['len'] == Total
        返回:
        - list: 包含所有队列名称的列表。
        """
        url = f"{self._rabbitmq_api_url}queues"
        try:
            response = requests.get(url, auth=self._auth)
            response.raise_for_status()  # 检查请求是否成功
            queue_info = response.json()
            if queue_name:
                return [q for q in queue_info if q['name'] == queue_name]
            else:
                return queue_info

        except requests.RequestException as e:
            rabbitmq_logger.error(
                f"Failed to connect to RabbitMQ Management API, retrying i")
        return []

    def get_all_exchanges(self, exchange_name=None,is_amq=False):
        """
        获取RabbitMQ中所有的交换机名称。

        返回:
        - list: 包含所有队列名称的列表。
        """
        url = f"{self._rabbitmq_api_url}exchanges"
        try:
            response = requests.get(url, auth=self._auth)
            response.raise_for_status()  # 检查请求是否成功
            exchange_info = response.json()
            if exchange_name:
                return [q for q in exchange_info if q['name'] == exchange_name]
            else:
                if is_amq:
                    return exchange_info
                else:
                    return [q for q in exchange_info if "amq" not in q['name']]
        except requests.RequestException as e:
            rabbitmq_logger.error(
                f"Failed to connect to RabbitMQ Management API, retrying i")
        return []

    def get_connections(self, host=None, user=None):
        """
        获取当前RabbitMQ服务器上的连接列表。

        通过RabbitMQ Management API获取当前的连接信息，并根据提供的主机或用户过滤结果。

        参数:
        - host (可选): 用于过滤连接的主机名称。
        - user (可选): 用于过滤连接的用户名。

        返回:
        - 如果提供了host或user参数，则返回匹配的连接列表。
        - 如果没有提供过滤条件，则返回所有连接的列表。
        - 在发生请求错误时，返回空列表，并记录错误信息。
        """
        # 构造请求连接的URL
        url = f"{self._rabbitMQ_api_url}connections"
        try:
            # 发送HTTP GET请求获取连接信息
            response = requests.get(url, auth=self._auth)
            # 检查请求是否成功
            response.raise_for_status()
            # 解析响应中的JSON数据，获取连接列表
            connections = response.json()
            # 根据提供的主机或用户参数进行过滤
            if host:
                return [q for q in connections if q['host'] == host]
            if user:
                return [q for q in connections if q['user'] == user]
            # 返回所有连接的列表
            return connections
        except requests.RequestException as e:
            # 在发生请求错误时，记录错误信息
            rabbitmq_logger.error(
                f"Failed to connect to RabbitMQ Management API, retrying in {self._retry_interval} seconds.")
        # 在发生错误时返回空列表

    def get_channels(self, user=None, state=None):
        """
        获取当前RabbitMQ服务器上的通道列表。

        通过RabbitMQ Management API获取当前的通道信息，并根据提供的通道名称或状态进行过滤。

        参数:
        - user (可选): 用于过滤连接的用户名。
        - state (可选): 用于过滤通道的状态。

        返回:
        - 如果提供了name或state参数，则返回匹配的通道列表。
        - 如果没有提供过滤条件，则返回所有通道的列表。
        - 在发生请求错误时，返回空列表，并记录错误信息。
        """
        # 构造请求通道的URL
        url = f"{self._rabbitmq_api_url}channels"
        try:
            # 发送HTTP GET请求获取通道信息
            response = requests.get(url, auth=self._auth)
            # 检查请求是否成功
            response.raise_for_status()
            # 解析响应中的JSON数据，获取通道列表
            channels = response.json()
            # 根据提供的通道名称或状态进行过滤
            if user:
                return [c for c in channels if c['user'] == user]
            if state:
                return [c for c in channels if c['state'] == state]
            # 返回所有通道的列表
            return channels
        except requests.RequestException as e:
            # 在发生请求错误时，记录错误信息
            rabbitmq_logger.error(
                f"Failed to connect to RabbitMQ Management API, retrying in {self._retry_interval} seconds.")
        # 在发生错误时返回空列表
        return []

    def migrate_rabbitmq(
        self,
        source_config,
        target_config,
        exchange_list: list | None = None,
        queue_list: list | None = None,
        not_exchange_list: list | None = None,
        not_queue_list: list | None = None,
        is_reserve=False,
    ):
        """
        迁移RabbitMQ的数据。

        根据提供的源和目标配置，以及可选的交换机和队列列表，迁移RabbitMQ的数据。
        可以选择性地删除源数据以同步目标数据。

        参数:
        - source_config: 源RabbitMQ的配置信息。
        - target_config: 目标RabbitMQ的配置信息。
        - exchange_list: 需要迁移的交换机列表。如果未提供，则迁移所有交换机。
        - queue_list: 需要迁移的队列列表。如果未提供，则迁移所有队列。
        - not_exchange_list: 不需要迁移的交换机列表。如果未提供，则不排除任何交换机。
        - not_queue_list: 不需要迁移的队列列表。如果未提供，则不排除任何队列。
        - is_reserve: 是否在迁移后保留源数据，默认为False。

        返回:
        无返回值。
        """
        # 创建源RabbitMQ管理器
        source_rabbitmq_manager = RabbitManager(rabbit_config=source_config)
        # 创建目标RabbitMQ管理器
        target_rabbitmq_manager = RabbitManager(rabbit_config=target_config)

        # 获取并筛选需要迁移的交换机
        source_all_exchanges = source_rabbitmq_manager.get_all_exchanges()
        if not_exchange_list:
            source_all_exchanges = [exchange for exchange in source_all_exchanges if exchange['name'] not in not_exchange_list]
        if exchange_list:
            source_all_exchanges = [exchange for exchange in source_all_exchanges if exchange['name'] in exchange_list]

        # 迁移交换机及其绑定的队列
        for source_exchange in source_all_exchanges:
            source_bing_queues = source_rabbitmq_manager.get_exchange_bindings(source_exchange['name'])
            if not_queue_list:
                source_bing_queues = [queue for queue in source_bing_queues if
                                        queue['routing_key'] not in not_queue_list]
            if queue_list:
                source_bing_queues = [queue for queue in source_bing_queues if
                                        queue['routing_key'] in queue_list]

            # 开始迁移
            for source_queue in source_bing_queues:
                # 在目标RabbitMQ声明交换机
                target_rabbitmq_manager.channel.exchange_declare(exchange=source_exchange['name'], exchange_type='direct', durable=True)
                # 在源RabbitMQ声明队列
                source_rabbitmq_manager_queue = source_rabbitmq_manager.channel.queue_declare(queue=source_queue['routing_key'],durable=True)
                # 迁移消息
                for _ in range(source_rabbitmq_manager_queue.method.message_count):
                    source_rabbitmq_manager.consume_tasks(exchange_name=source_exchange['name'], queue_name=source_queue['routing_key'])
                    target_rabbitmq_manager.send_task(source_rabbitmq_manager.received_body, source_exchange['name'],source_queue['routing_key'])
                    # 如果需要保留源数据，则重新发送消息到源RabbitMQ
                    if is_reserve:
                        source_rabbitmq_manager.send_task(source_rabbitmq_manager.received_body,source_exchange['name'], source_queue['routing_key'])

    def get_queue_num(self, queue_name):
        """
        声明队列并获取队列中的消息数量。

        参数:
        queue_name (str): 队列的名称。

        返回:
        int: 队列中的消息数量。
        """
        # 声明队列并获取队列信息
        queue = self.channel.queue_declare(queue=queue_name, durable=True)
        # 获取队列中的消息数量
        queue_num = queue.method.message_count
        return queue_num

    def get_queue_consumer_count(self, queue_name):
        """
        获取指定队列的消费者数量

        :param queue_name: 队列名称，用于指定要查询的队列
        :return: 返回指定队列的消费者数量
        """
        # 声明队列并获取队列信息
        queue = self.channel.queue_declare(queue=queue_name, durable=True)
        # 获取队列中的消费者数量
        consumer_count = queue.method.consumer_count
        return consumer_count



class RabbitConfig:
    def __init__(self, **keyword):
        """
        初始化 RabbitMQ 配置

        :param db_settings: 包含 RabbitMQ 配置的设置对象
        """
        self.host = keyword.get("host", mqSettings.host)
        self.port = keyword.get("port", mqSettings.port)
        self.user = keyword.get("user", mqSettings.user)
        self.password = keyword.get("password", mqSettings.password)
        self.api_port = keyword.get("api_port", mqSettings.api_port)
        self.virtual_host = keyword.get("virtual_host", mqSettings.virtual_host)
        self.connection_attempts = keyword.get("connection_attempts", mqSettings.connection_attempts)
        self.retry_delay = keyword.get("retry_delay", mqSettings.retry_delay)
        self.socket_timeout = keyword.get("socket_timeout", mqSettings.socket_timeout)
        self.max_rebbitmq_prefetch_count = keyword.get("max_rebbitmq_prefetch_count",
                                                       mqSettings.prefetch_count)
        self.max_consumer = keyword.get("max_consumer", mqSettings.max_consumer)
        self.heartbeat = keyword.get("heartbeat", mqSettings.heartbeat)
        self.blocked_connection_timeout = keyword.get("blocked_connection_timeout", mqSettings.blocked_connection_timeout)
        self.rabbitmq_pool_max_overflow = keyword.get("rabbitmq_pool_max_overflow", mqSettings.pool_max_overflow)

    def to_dict(self):
        """
        将配置转换为字典

        :return: 包含所有配置的字典
        """
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "api_port": self.api_port,
            "virtual_host":self.virtual_host,
            "connection_attempts": self.connection_attempts,
            "retry_delay": self.retry_delay,
            "socket_timeout": self.socket_timeout,
            "max_rebbitmq_prefetch_count": self.max_rebbitmq_prefetch_count,
            "max_consumer": self.max_consumer,
            "heartbeat": self.heartbeat,
            "rabbitmq_pool_max_overflow": self.rabbitmq_pool_max_overflow,
            "blocked_connection_timeout":self.blocked_connection_timeout
        }

class RabbitMQConnectionPool:
    """
    RabbitMQ连接池类，用于管理和复用RabbitMQ连接。

    属性:
    - _pool_size (int): 连接池的最大连接数。
    - _connections (list): 存储连接的列表，每个元素是一个 (connection, lock) 元组。
    - _params (pika.ConnectionParameters): 连接参数。
    - _lock (threading.Lock): 用于保护连接池的锁。

    方法:
    - __init__: 初始化连接池。
    - _create_connection: 创建一个新的RabbitMQ连接。
    - _get_connection: 获取一个可用的RabbitMQ连接。
    - _release_connection: 释放一个RabbitMQ连接回连接池。
    - close: 关闭所有连接并清理资源。
    - connection: 上下文管理器，用于 `with` 语句。
    - get_connection: 获取一个RabbitMQ连接。
    - release_connection: 释放一个RabbitMQ连接。
    """

    def __init__(self, rabbit_config, pool_size=10):
        """
        初始化RabbitMQ连接池。

        参数:
        - host (str): RabbitMQ服务器地址。
        - port (int): RabbitMQ服务器端口。
        - username (str): 用户名。
        - password (str): 密码。
        - virtual_host (str): 虚拟主机，默认为 '/'。
        - pool_size (int): 连接池大小，默认为 10。
        """
        self._pool_size = pool_size
        self._connections = []
        self.rabbit_config = rabbit_config
        self._lock = threading.Lock()

    def _create_connection(self):
        """
        创建一个新的RabbitMQ连接。

        返回:
        - connection (pika.BlockingConnection): 新创建的RabbitMQ连接。
        """
        return RabbitManager(self.rabbit_config)

    def _get_connection(self):
        """
        获取一个可用的RabbitMQ连接。

        返回:
        - connection (pika.BlockingConnection): 可用的RabbitMQ连接。
        """
        with self._lock:
            if self._connections:
                # 随机从连接池中获取一个连接
                index = random.randint(0, len(self._connections) - 1)
                connection, lock = self._connections.pop(index)
                # 检查当前连接的状态，如果连接或通道任一未开启，则关闭旧连接并创建新的连接
                if not (connection.connection.is_open and connection.channel.is_open):
                    try:
                        connection.close()
                    except Exception as e:
                        print(f"Failed to close connection: {e}")
                    connection = self._create_connection()
                lock.acquire()  # 加锁
                return connection, lock
            elif len(self._connections) < self._pool_size:
                # 创建新的连接
                connection = self._create_connection()
                lock = threading.Lock()
                lock.acquire()  # 加锁
                return connection, lock
            else:
                raise Exception("Too many connections, connection pool is full")

    def _release_connection(self, connection, lock):
        """
        释放一个RabbitMQ连接回连接池。

        参数:
        - connection (pika.BlockingConnection): 要释放的RabbitMQ连接。
        - lock (threading.Lock): 连接的锁。
        """
        with self._lock:
            lock.release()  # 释放锁
            self._connections.append((connection, lock))

    def close(self,connection=None):
        """
        关闭所有连接并清理资源。
        """
        with self._lock:
            if connection:
                connection.close()
            else:
                for connection, lock in self._connections:
                    connection.close()
                self._connections.clear()

    @contextlib.contextmanager
    def connection(self):
        """
        上下文管理器，用于 `with` 语句。

        使用示例:
        """
        # 进入 with 语句块时执行的代码
        conn, lock = self._get_connection()
        try:
            yield conn
        except (pika.exceptions.ChannelWrongStateError, pika.exceptions.ConnectionWrongStateError) as e:
            print(f"Connection error: {e}")
            # 尝试重新获取连接
            conn, lock = self._get_connection()
        finally:
            # 退出 with 语句块时执行的代码
            self._release_connection(conn, lock)

    def get_connection(self):
        """
        获取一个RabbitMQ连接。

        返回:
        - connection (pika.BlockingConnection): 可用的RabbitMQ连接。
        """
        conn, lock = self._get_connection()
        return conn, lock

    def release_connection(self, connection, lock):
        """
        释放一个RabbitMQ连接。

        参数:
        - connection (pika.BlockingConnection): 要释放的RabbitMQ连接。
        - lock (threading.Lock): 连接的锁。
        """
        self._release_connection(connection, lock)

rabbit_config = RabbitConfig().to_dict()
rabbit_pool = RabbitMQConnectionPool(rabbit_config,pool_size=rabbit_config.get("rabbitmq_pool_max_overflow",10))


__all__ = [
    "rabbit_pool",
    "RabbitConfig",
    "RabbitManager",
    "rabbit_config",
    "RabbitMQConnectionPool",
]




