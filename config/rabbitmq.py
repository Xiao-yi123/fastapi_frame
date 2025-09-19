import asyncio
import contextlib
import json

import threading
import time
import pika
import requests
from typing import Optional, Any, Union, Generator

from app.logs import rabbitmq_logger
from config.settings import mqSettings

class RabbitConfig:
    def __init__(self, rabbit_config: dict = mqSettings.RabbitMq):
        """
        初始化 RabbitMQ 配置

        :param rabbit_config: RabbitMQ 配置字典，如果为 None 则使用默认设置
        """
        self.rabbit_config = rabbit_config
        self.current_key = None

    def config_to_dict(self, **overrides) -> dict:
        """
        将配置转换为字典，支持覆盖默认值

        :param overrides: 要覆盖的配置项
        :return: 包含所有配置的字典
        """
        base_config = {
            "host": mqSettings.host,
            "port": mqSettings.port,
            "user": mqSettings.user,
            "password": mqSettings.password,
            "api_port": mqSettings.api_port,
            "virtual_host": mqSettings.virtual_host,
            "connection_attempts": mqSettings.connection_attempts,
            "retry_delay": mqSettings.retry_delay,
            "socket_timeout": mqSettings.socket_timeout,
            "max_rebbitmq_prefetch_count": mqSettings.prefetch_count,
            "max_consumer": mqSettings.max_consumer,
            "heartbeat": mqSettings.heartbeat,
            "blocked_connection_timeout": mqSettings.blocked_connection_timeout,
            "rabbitmq_pool_max_overflow": mqSettings.pool_max_overflow
        }

        # 应用覆盖值
        base_config.update(overrides)
        return base_config

    def use_key(self, key: str) -> 'RabbitConfig':
        """
        设置要使用的配置键

        :param key: 配置键名
        :return: self (支持链式调用)
        """
        self.current_key = self.rabbit_config.get(key)
        return self

    def get_config(self) -> dict:
        """
        获取当前配置键的完整配置

        :return: 配置字典
        """
        if not self.current_key:
            raise ValueError("No key selected. Use use_key() first.")
        return self.current_key.__dict__ if hasattr(self.current_key, '__dict__') else self.current_key

    def get_exchange_name(self) -> str:
        """
        获取交换机名称

        :return: 交换机名称
        """
        config = self.get_config()
        return config.get('exchange_name')

    def get_not_control_queues(self) -> list:
        """
        获取不监控的队列列表

        :return: 不监控的队列名称列表
        """
        config = self.get_config()
        return config.get('not_control', [])

    def get_start_monitoring_queues(self, queue_name: str = None) -> Union[dict, list]:
        """
        获取启动监控的队列配置

        :param queue_name: 可选，指定队列名称
        :return: 队列配置字典或列表
        """
        config = self.get_config()
        queues = config.get('queue_start_monitoring', {})

        if queue_name:
            queue_obj = queues.get(queue_name)
            return queue_obj.__dict__ if queue_obj and hasattr(queue_obj, '__dict__') else queue_obj
        return {name: q.__dict__ if hasattr(q, '__dict__') else q for name, q in queues.items()}

    def get_monitor_queues(self, queue_name: str = None) -> Union[dict, list]:
        """
        获取监控队列配置

        :param queue_name: 可选，指定队列名称
        :return: 队列配置字典或列表
        """
        config = self.get_config()
        queues = config.get('queue_monitor_queue', [])

        if queue_name:
            for queue in queues:
                q_dict = queue.__dict__ if hasattr(queue, '__dict__') else queue
                if q_dict.get('queue_name') == queue_name:
                    return q_dict
            return None

        return [q.__dict__ if hasattr(q, '__dict__') else q for q in queues]

    def get_config_types(self) -> list:
        """
        获取配置类型列表

        :return: 配置类型列表
        """
        config = self.get_config()
        return config.get('type', [])

    def has_config_type(self, config_type: str) -> bool:
        """
        检查是否包含指定的配置类型

        :param config_type: 配置类型
        :return: 是否包含
        """
        return config_type in self.get_config_types()

    def is_start_monitoring_enabled(self) -> bool:
        """
        检查是否启用了启动监控

        :return: 是否启用
        """
        return self.has_config_type('start_monitoring')

    def is_monitor_queue_enabled(self) -> bool:
        """
        检查是否启用了队列监控

        :return: 是否启用
        """
        return self.has_config_type('monitor_queue')

    def get_all_queue_names(self, include_not_control: bool = False) -> list:
        """
        获取所有队列名称

        :param include_not_control: 是否包含不监控的队列
        :return: 队列名称列表
        """
        queue_names = []

        # 获取启动监控的队列
        start_queues = self.get_start_monitoring_queues()
        if isinstance(start_queues, dict):
            queue_names.extend(start_queues.keys())

        # 获取监控队列
        monitor_queues = self.get_monitor_queues()
        if isinstance(monitor_queues, list):
            for queue in monitor_queues:
                if isinstance(queue, dict) and 'queue_name' in queue:
                    queue_names.append(queue['queue_name'])

        # 过滤不监控的队列
        if not include_not_control:
            not_control = self.get_not_control_queues()
            queue_names = [name for name in queue_names if name not in not_control]

        return list(set(queue_names))  # 去重

    def get_is_create_task_by_exchange_and_queue(self, exchange_name: str, queue_name: str) -> bool:
        """
        通过交换机名和队列名获取是否需要创建key（无需知道key）

        :param exchange_name: 交换机名称
        :param queue_name: 队列名称
        :return:
        """
        for key, config_value in self.rabbit_config.items():
            # 将配置对象转换为字典
            config_dict = config_value.__dict__ if hasattr(config_value, '__dict__') else config_value

            # 检查交换机名称是否匹配
            if config_dict.get('exchange_name') == exchange_name:
                # 检查启动监控队列
                start_queues = config_dict.get('queue_start_monitoring', {})
                for q_key, q_value in start_queues.items():
                    q_dict = q_value.__dict__ if hasattr(q_value, '__dict__') else q_value
                    if q_dict.get('queue_name') == queue_name:
                        return True

                # 检查监控队列
                monitor_queues = config_dict.get('queue_monitor_queue', [])
                for queue in monitor_queues:
                    q_dict = queue.__dict__ if hasattr(queue, '__dict__') else queue
                    if q_dict.get('queue_name') == queue_name:
                        return True

        return False

class RabbitManager:
    def __init__(self, rabbit_config: RabbitConfig):
        self._create_key_dict = dict() # 创建key的dict 在run_def 内使用
        self._build_create_key_dict(rabbit_config.rabbit_config)
        # 配置初始化
        self._config = rabbit_config.config_to_dict()
        self._rabbitmq_host = self._config.get('host', "127.0.0.1")
        self._rabbitmq_port = self._config.get('port', 5672)
        self._rabbitmq_user = self._config.get('user')
        self._rabbitmq_password = self._config.get('password')
        self._rabbitmq_api_port = self._config.get('api_port', 15672)
        self._virtual_host = self._config.get('virtual_host', "/")
        self._max_rebbitmq_prefetch_count = self._config.get('max_rebbitmq_prefetch_count', 3)
        self._max_consumer = self._config.get("max_consumer", 5)

        # 连接参数
        self._heartbeat = self._parse_int(self._config.get("heartbeat"))
        self._blocked_connection_timeout = self._parse_int(self._config.get('blocked_connection_timeout'))
        self.connection_attempts = self._config.get('connection_attempts', 10)
        self.retry_delay = self._config.get('retry_delay', 5)
        self.socket_timeout = self._config.get('socket_timeout', 10)

        # API 配置
        self._rabbitmq_api_url = f"http://{self._rabbitmq_host}:{self._rabbitmq_api_port}/api/"
        self._auth = (self._rabbitmq_user,
                      self._rabbitmq_password) if self._rabbitmq_user and self._rabbitmq_password else None

        # 状态变量
        self.received_body = None
        self._is_init_exchange_and_queue = False

        # 连接
        self.connection, self.channel = self.connect_to_rabbitmq()
    def _build_create_key_dict(self, rabbit_config):
        for key, config_value in rabbit_config.items():
            exchange_name = config_value.exchange_name
            # 检查启动监控队列
            for q_key, q_value in config_value.queue_start_monitoring.items():
                if q_value.is_create_task:
                    self._create_key_dict[f"{exchange_name}_{q_value.queue_name}"] = q_value
                    print(q_value)
                    print(q_value.queue_fun)
    def _parse_int(self, value) -> Optional[int]:
        """安全解析整数值"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _init_exchange_and_queue(self, exchange_name: str, queue_name: str):
        """初始化交换机和队列"""
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type='direct',
                durable=True
            )
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name)
            self.channel.basic_qos(prefetch_count=self._max_rebbitmq_prefetch_count)
            self._is_init_exchange_and_queue = True
        except Exception as e:
            rabbitmq_logger.error(f"Failed to initialize exchange and queue: {e}")
            raise

    def close(self):
        """安全关闭连接"""
        try:
            if hasattr(self, 'channel') and self.channel and self.channel.is_open:
                self.channel.close()
        except Exception as e:
            rabbitmq_logger.debug(f"Error closing channel: {e}")

        try:
            if hasattr(self, 'connection') and self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            rabbitmq_logger.debug(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_task(self, function_name: str, *args, **kwargs) -> dict:
        """创建任务字典"""
        return {
            "function_name": function_name,
            "args": args,
            "kwargs": kwargs
        }

    def connect_to_rabbitmq(self, max_retries: int = 5, retry_delay: int = 5):
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
        rabbitmq_params = pika.ConnectionParameters(
            host=self._rabbitmq_host,
            port=self._rabbitmq_port,
            virtual_host=self._virtual_host,
            credentials=pika.PlainCredentials(self._rabbitmq_user, self._rabbitmq_password),
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
            socket_timeout=self.socket_timeout,
            heartbeat=self._heartbeat,
            blocked_connection_timeout=self._blocked_connection_timeout
        )

        for attempt in range(max_retries):
            try:
                connection = pika.BlockingConnection(rabbitmq_params)
                channel = connection.channel()
                rabbitmq_logger.info(f"Successfully connected to RabbitMQ (attempt {attempt + 1})")
                return connection, channel
            except pika.exceptions.AMQPConnectionError as e:
                rabbitmq_logger.warning(
                    f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {retry_delay} seconds: {e}"
                )
                time.sleep(retry_delay)

        raise RuntimeError(f"Failed to connect to RabbitMQ after {max_retries} attempts")

    def send_task(self, task: dict, exchange_name: str = '', queue_name: str = ''):
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
        try:
            # 声明交换机和队列
            self.channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name)

            # 发送消息
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=queue_name,
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            if isinstance(task, dict) and task.get("function_name"):
                rabbitmq_logger.debug(
                    f"Sent task: exchange={exchange_name}, queue={queue_name}, "
                    f"function={task.get('function_name')}"
                )

        except Exception as e:
            rabbitmq_logger.error(f"Failed to send task: {e}")
            raise

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
        try:
            task = json.loads(body)
            self.received_body = task
            # 创建任务字典
            dict_key = f"{method.exchange}_{method.routing_key}"
            if dict_key in self._create_key_dict.keys():
                task = self.create_task(function_name=self._create_key_dict[dict_key].queue_fun,args=task.get("args"),kwargs=task)

            # 验证任务字典
            if isinstance(task, dict) and task.get("function_name"):
                rabbitmq_logger.debug(
                    f"Received task: exchange={method.exchange}, "
                    f"queue={method.routing_key}, function={task.get('function_name')}"
                )
            # 运行任务
            self._run_def(task, ch)

        except json.JSONDecodeError as e:
            rabbitmq_logger.error(f"Failed to parse task JSON: {e}, body: {body}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            rabbitmq_logger.error(f"Error processing task: {type(e).__name__} - {e}, body: {body}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def _run_def(self, task: dict, ch=None):
        """
        执行定义的函数。

        从任务字典中提取函数名、位置参数和关键字参数，并尝试执行该函数。
        如果函数名未定义或执行过程中出现异常，则根据情况返回任务字典或停止消费。

        参数:
        - task: 包含函数名、位置参数和关键字参数的任务字典。
        - ch: 消息队列通道对象，用于停止消费操作。
        - method: 方法框，包含方法的属性

        返回:
        无返回值。根据执行情况更新 self.received_body 或停止消费。
        """
        try:
            function_name = task.get("function_name")
            args = task.get("args", [])
            kwargs = task.get("kwargs", {})

            if function_name is None:
                self.received_body = task
                if ch:
                    ch.stop_consuming()
                return

            func = globals().get(function_name)
            if not func:
                rabbitmq_logger.error(f"Function '{function_name}' not found")
                return

            # 执行函数
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)

        except Exception as e:
            rabbitmq_logger.error(f"Error executing function: {e}")
            raise

    def consume_tasks(self, exchange_name: str = "", queue_name: str = ''):
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

            self.channel.basic_consume(queue=queue_name, on_message_callback=self.process_task)
            self.channel.start_consuming()

        except Exception as e:
            self._is_init_exchange_and_queue = False
            rabbitmq_logger.error(f"Error while consuming tasks: {e}")
            raise

    def start_monitoring(self, exchange_name: str, queue_name: dict = None, not_control: list = []):
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
        for queue in queue_name.values():
            if queue.queue_name in not_control:
                continue

            for n in range(queue.max_consumer if queue.max_consumer else self._max_consumer):
                threading_name = f"{exchange_name}-{queue.queue_name}-{n}"
                consumer_thread = threading.Thread(
                    target=self.consume_tasks,
                    name=threading_name,
                    daemon=True,
                    args=(exchange_name, queue.queue_name)
                )
                consumer_thread.start()

    def clear_and_delete_queues(self, exchange_name: str, queue_name: str = None,
                                is_delete_exchange: bool = False, is_delete_queue: bool = False):
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
        queue_names = [queue['routing_key'] for queue in self.get_exchange_bindings(exchange_name)]

        if queue_name:
            if queue_name in queue_names:
                self.clear_queue(queue_name, is_delete=is_delete_queue)
        else:
            for q_name in queue_names:
                self.clear_queue(q_name, is_delete=is_delete_queue)

        if is_delete_exchange:
            try:
                self.channel.exchange_delete(exchange_name)
            except Exception as e:
                rabbitmq_logger.error(f"Failed to delete exchange {exchange_name}: {e}")

    def clear_queue(self, queue_name: str, is_delete: bool = False):
        """
        清空指定的RabbitMQ队列。

        参数:
        - channel: 已经建立好的RabbitMQ通道。
        - queue_name (str): 需要清空的队列名称。
        - is_delete (bool): 是否删除
        注意:
        - 此函数假定已经有一个有效的channel连接。
        """
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)

            while True:
                method_frame, header_frame, body = self.channel.basic_get(queue=queue_name, auto_ack=True)
                if method_frame is None:
                    break

            if is_delete:
                self.channel.queue_delete(queue=queue_name)

        except Exception as e:
            rabbitmq_logger.error(f"Failed to clear queue {queue_name}: {e}")

    def get_exchange_bindings(self, exchange_name: str = None) -> list:
        """
        获取所有绑定列表或者指定的绑定列表

        参数:
        exchange_name (str): 交换机名称。如果不指定，则返回所有交换机下的队列；否则返回指定交换机下的队列。

        返回:
        list: 绑定到指定交换机的队列列表。如果未找到任何队列或请求失败，则返回空列表。
        """
        try:
            url = f"{self._rabbitmq_api_url}bindings"
            if exchange_name:
                url += f"?source={exchange_name}"

            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()

            bindings = response.json()
            if exchange_name:
                return [binding for binding in bindings if binding.get("source") == exchange_name]
            return bindings

        except requests.RequestException as e:
            rabbitmq_logger.error(f"Failed to fetch bindings for exchange {exchange_name}: {e}")
            return []

    def get_all_queues(self, queue_name: str = None) -> list:
        """
        获取RabbitMQ中所有的队列信息或者指定。
        result['backing_queue_status']['len'] == Ready
        result['backing_queue_status']['num_pending_acks'] == Unacked
        result['backing_queue_status']['num_pending_acks'] + result['backing_queue_status']['len'] == Total
        返回:
        - list: 包含所有队列名称的列表。
        """
        try:
            url = f"{self._rabbitmq_api_url}queues"
            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()

            queue_info = response.json()
            if queue_name:
                return [q for q in queue_info if q['name'] == queue_name]
            return queue_info

        except requests.RequestException as e:
            rabbitmq_logger.error(f"Failed to get queues: {e}")
            return []

    def get_all_exchanges(self, exchange_name: str = None, is_amq: bool = False) -> list:
        """
        获取RabbitMQ中所有的交换机名称。

        返回:
        - list: 包含所有队列名称的列表。
        """
        try:
            url = f"{self._rabbitmq_api_url}exchanges"
            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()

            exchange_info = response.json()
            if exchange_name:
                return [q for q in exchange_info if q['name'] == exchange_name]

            if is_amq:
                return exchange_info
            else:
                return [q for q in exchange_info if "amq" not in q['name']]

        except requests.RequestException as e:
            rabbitmq_logger.error(f"Failed to get exchanges: {e}")
            return []

    def get_connections(self, host: str = None, user: str = None) -> list:
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
        try:
            url = f"{self._rabbitmq_api_url}connections"
            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()

            connections = response.json()
            if host:
                return [q for q in connections if q.get('host') == host]
            if user:
                return [q for q in connections if q.get('user') == user]
            return connections

        except requests.RequestException as e:
            rabbitmq_logger.error(f"Failed to get connections: {e}")
            return []

    def get_channels(self, user: str = None, state: str = None) -> list:
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
        try:
            url = f"{self._rabbitmq_api_url}channels"
            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()

            channels = response.json()
            if user:
                return [c for c in channels if c.get('user') == user]
            if state:
                return [c for c in channels if c.get('state') == state]
            return channels

        except requests.RequestException as e:
            rabbitmq_logger.error(f"Failed to get channels: {e}")
            return []

    def migrate_rabbitmq(self, source_config: RabbitConfig, target_config: RabbitConfig,
                         exchange_list: list = None, queue_list: list = None,
                         not_exchange_list: list = None, not_queue_list: list = None,
                         is_reserve: bool = False):
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
        source_manager = RabbitManager(rabbit_config=source_config)
        target_manager = RabbitManager(rabbit_config=target_config)

        source_all_exchanges = source_manager.get_all_exchanges()

        # 过滤交换机
        if not_exchange_list:
            source_all_exchanges = [ex for ex in source_all_exchanges if ex['name'] not in not_exchange_list]
        if exchange_list:
            source_all_exchanges = [ex for ex in source_all_exchanges if ex['name'] in exchange_list]

        for source_exchange in source_all_exchanges:
            source_bind_queues = source_manager.get_exchange_bindings(source_exchange['name'])

            # 过滤队列
            if not_queue_list:
                source_bind_queues = [q for q in source_bind_queues if q['routing_key'] not in not_queue_list]
            if queue_list:
                source_bind_queues = [q for q in source_bind_queues if q['routing_key'] in queue_list]

            for source_queue in source_bind_queues:
                try:
                    target_manager.channel.exchange_declare(
                        exchange=source_exchange['name'],
                        exchange_type='direct',
                        durable=True
                    )

                    source_queue_info = source_manager.channel.queue_declare(
                        queue=source_queue['routing_key'],
                        durable=True
                    )

                    for _ in range(source_queue_info.method.message_count):
                        source_manager.consume_tasks(
                            exchange_name=source_exchange['name'],
                            queue_name=source_queue['routing_key']
                        )

                        target_manager.send_task(
                            source_manager.received_body,
                            source_exchange['name'],
                            source_queue['routing_key']
                        )

                        if is_reserve:
                            source_manager.send_task(
                                source_manager.received_body,
                                source_exchange['name'],
                                source_queue['routing_key']
                            )

                except Exception as e:
                    rabbitmq_logger.error(f"Failed to migrate queue {source_queue['routing_key']}: {e}")

        source_manager.close()
        target_manager.close()

    def get_queue_num(self, queue_name: str) -> int:
        """
        声明队列并获取队列中的消息数量。

        参数:
        queue_name (str): 队列的名称。

        返回:
        int: 队列中的消息数量。
        """
        try:
            queue = self.channel.queue_declare(queue=queue_name, durable=True)
            return queue.method.message_count
        except Exception as e:
            rabbitmq_logger.error(f"Failed to get queue count for {queue_name}: {e}")
            return 0

    def get_queue_consumer_count(self, queue_name: str) -> int:
        """
        获取指定队列的消费者数量

        :param queue_name: 队列名称，用于指定要查询的队列
        :return: 返回指定队列的消费者数量
        """
        try:
            queue = self.channel.queue_declare(queue=queue_name, durable=True)
            return queue.method.consumer_count
        except Exception as e:
            rabbitmq_logger.error(f"Failed to get consumer count for {queue_name}: {e}")
            return 0


class RabbitMQConnectionPool:
    """
    RabbitMQ连接池类，用于管理和复用RabbitMQ连接
    """

    def __init__(self, rabbit_config: RabbitConfig, pool_size: int = 10):
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
        self.pool_size = pool_size
        self.rabbit_config = rabbit_config
        self._connections = []
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._active_connections = 0

    def _create_connection(self) -> RabbitManager:
        """
        创建一个新的RabbitMQ连接。

        返回:
        - connection (pika.BlockingConnection): 新创建的RabbitMQ连接。
        """
        return RabbitManager(self.rabbit_config)

    def _is_connection_valid(self, connection: RabbitManager) -> bool:
        """检查连接是否有效"""
        try:
            return (connection.connection and connection.connection.is_open and
                    connection.channel and connection.channel.is_open)
        except Exception:
            return False

    @contextlib.contextmanager
    def get_connection(self) -> Generator[RabbitManager | Any, Any, None]:
        """
        获取一个RabbitMQ连接（上下文管理器方式）
        """
        connection = None

        with self._condition:
            # 等待可用连接
            while len(self._connections) == 0 and self._active_connections >= self.pool_size:
                self._condition.wait()

            if self._connections:
                connection, lock = self._connections.pop()
            else:
                connection = self._create_connection()
                lock = threading.Lock()

            self._active_connections += 1

        try:
            # 检查连接有效性
            if not self._is_connection_valid(connection):
                connection.close()
                connection = self._create_connection()

            lock.acquire()
            yield connection

        except Exception as e:
            rabbitmq_logger.error(f"Error using connection: {e}")
            # 创建新连接替换失效的连接
            connection.close()
            connection = self._create_connection()
            yield connection

        finally:
            lock.release()
            with self._condition:
                self._active_connections -= 1
                if self._is_connection_valid(connection):
                    self._connections.append((connection, lock))
                else:
                    connection.close()
                self._condition.notify()

    def get_connection_nowait(self) -> tuple:
        """立即获取连接（不等待）"""
        with self._condition:
            if self._connections:
                connection, lock = self._connections.pop()
                self._active_connections += 1
                lock.acquire()
                return connection, lock
            elif self._active_connections < self.pool_size:
                connection = self._create_connection()
                lock = threading.Lock()
                self._active_connections += 1
                lock.acquire()
                return connection, lock
            else:
                raise Exception("Connection pool exhausted")

    def release_connection(self, connection: RabbitManager, lock: threading.Lock):
        """
        释放一个RabbitMQ连接回连接池。

        参数:
        - connection (pika.BlockingConnection): 要释放的RabbitMQ连接。
        - lock (threading.Lock): 连接的锁。
        """
        try:
            lock.release()
            with self._condition:
                if self._is_connection_valid(connection):
                    self._connections.append((connection, lock))
                else:
                    connection.close()
                self._active_connections -= 1
                self._condition.notify()
        except Exception as e:
            rabbitmq_logger.error(f"Error releasing connection: {e}")
            connection.close()

    def close_all(self):
        """关闭所有连接"""
        with self._condition:
            for connection, lock in self._connections:
                try:
                    connection.close()
                except Exception as e:
                    rabbitmq_logger.debug(f"Error closing connection: {e}")
            self._connections.clear()
            self._active_connections = 0

    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        with self._condition:
            return {
                "total_size": self.pool_size,
                "available": len(self._connections),
                "active": self._active_connections,
                "max_used": self._active_connections - len(self._connections)
            }

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close_all()


# 全局配置
# rabbit_config = RabbitConfig()
# RabbitPool = RabbitMQConnectionPool(
#     RabbitConfig(),
#     pool_size=RabbitConfig().config_to_dict().get("rabbitmq_pool_max_overflow", 10)
# )

__all__ = [
    # "RabbitPool",
    "RabbitConfig",
    "RabbitManager",
    "RabbitMQConnectionPool",
]

if __name__ == '__main__':
    # 初始化
    config = RabbitConfig()

    # 使用特定键
    config.use_key("task")

    # 获取基本信息
    exchange_name = config.get_exchange_name()
    not_control_queues = config.get_not_control_queues()

    # 获取队列配置
    start_queues = config.get_start_monitoring_queues()
    specific_queue = config.get_start_monitoring_queues("collection_comment")

    # 检查配置类型
    if config.is_start_monitoring_enabled():
        print("启用了启动监控")

    # 获取所有队列名称
    all_queues = config.get_all_queue_names()

    # 链式调用
    queue_info = (RabbitConfig()
                  .use_key("task")
                  .get_start_monitoring_queues("collection_comment"))
