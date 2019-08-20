# -*- coding: utf-8 -*-
from pika.exceptions import AMQPConnectionError as BrokerConnectonException
from datetime import datetime
from .rabbitmq_config import RABBITMQ_BROKER, TASK_SERVICE
from .utils import get_service_addr

import base64
import importlib
import json
import logging
import os
import pika
import time
import requests
import importlib
import functools
import threading

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='rabbitmq_consumer.log',
                    filemode='a')

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)


class RabbitMQConsumer(object):
    """
    rabitmq消费者
    """

    def __init__(self, queue, rabbitmq_config=None, update_task=True, task_service_config=None):
        """
        输入参数说明：
        queue:  定义consumer所在队列
        rabbitmq_config: rabbitmq链接配置。不传则使用默认
        update_task: 是否在执行完更新task数据库
        task_service_config: 如果需要更新task数据库，则需要传入更新接口。不传则使用默认
        """
        # 检查queue的定义，已经queue是否已经存在在broker中
        rabbitmq = RABBITMQ_BROKER
        if not rabbitmq_config:
            logger.info("rabbitmq_config not defined, use default setting: {0}".format(
                RABBITMQ_BROKER))
        else:
            if not isinstance(rabbitmq_config, dict):
                raise Exception("rabbitmq_config is not type of dict")
            for key, value in rabbitmq_config.items():
                rabbitmq[key] = value

        if not queue:
            raise Exception("queue is not defined")
        self.update_task = update_task
        if self.update_task:
            task_service = TASK_SERVICE
            if task_service_config:
                for key, value in task_service_config.items():
                    task_service[key] = value
            else:
                logger.info(
                    "task_service_config not defined, use default config: {0}".format(task_service_config))
            self._task_api = self.get_task_api(task_service)
        else:
            self._task_api = None
        self.rabbitmq_url(rabbitmq)
        # 检查queue的定义，已经queue是否已经存在在broker中
        if not self.validate_queue(queue):
            raise Exception(
                "queue {0} is not defined in rabbitmq broker".format(queue))
        self._queue = queue
        # 最终执行任务的函数
        self._target_func_map = None

    def get_task_api(self, task_service_config):
        task_url = get_service_addr(task_service_config)
        task_api = "http://{0}{1}".format(task_url,
                                          task_service_config['UPDATE_TASK_API'])
        return task_api

    def rabbitmq_url(self, rabbitmq_config):
        # import pdb; pdb.set_trace()
        try:
            rabbitmq_url = get_service_addr(rabbitmq_config)
            addr = rabbitmq_url.split(':')[0]
            port = rabbitmq_url.split(':')[1]
            api_port = rabbitmq_config['API_PORT']
            user = rabbitmq_config['USER']
            password = rabbitmq_config['PASSWORD']
            vhost = rabbitmq_config.get('VHOST')
            if vhost:
                url = 'amqp://{user}:{password}@{addr}:{port}/{vhost}'.format(
                    user=user, password=password, addr=addr, port=port, vhost=vhost)
                api_url = 'http://{addr}:{port}/api/'.format(
                    addr=addr, port=api_port, vhost=vhost)
                queue_api_url = 'http://{addr}:{port}/api/queues/{vhost}'.format(
                    addr=addr, port=api_port, vhost=vhost)
            else:
                url = 'amqp://{user}:{password}@{addr}:{port}'.format(
                    user=user, password=password, port=port, addr=addr)
                api_url = 'http://{addr}:{port}/api'.format(
                    addr=addr, port=api_port)
                queue_api_url = 'http://{addr}:{port}/api/queues'.format(
                    addr=addr, port=api_port)
        except Exception as ex:
            raise Exception(ex)
        self._rabbitmq_user = user
        self._rabbitmq_password = password
        self._rabbitmq_addr = addr
        self._rabbitmq_port = port
        self._connection_url = url
        self._api_url = api_url
        self._queue_api_url = queue_api_url

    def validate_queue(self, queue):
        api_url = self._queue_api_url
        response = requests.get(api_url, auth=(
            self._rabbitmq_user, self._rabbitmq_password))
        if response.status_code != 200:
            return False

        available_queues = [queue['name'] for queue in response.json()]
        if queue in available_queues:
            return True
        return False

    @functools.lru_cache(maxsize=None)
    def get_target_func(self, func_name):
        # print("==========调用get_target_func, func_name={}".format(func_name))
        try:
            module_path, cls_name = func_name.rsplit(".", 1)
            func = getattr(importlib.import_module(module_path), cls_name)
        except:
            raise Exception(
                "模块{}路径错误或者不存在".format(func_name))
        return func

    def _get_target_func_map(self):
        return self._target_func_map

    def _set_target_func_map(self, target_func_map):
        for func in target_func_map.values():
            self.get_target_func(func)

        self._target_func_map = target_func_map

    target_func_map = property(_get_target_func_map, _set_target_func_map)

    def ack_message(self, channel, delivery_tag):
        """Note that `channel` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if channel.is_open:
            channel.basic_ack(delivery_tag)
        else:
            # Channel is already closed, so we can't ACK this message;
            logger.error(
                'channel is closed, delivery_tag {0} cannot be ACKed'.format(delivery_tag))

    def do_work(self, connection, channel, method_frame, header_frame, body):

        thread_id = threading.get_ident()
        delivery_tag = method_frame.delivery_tag
        fmt1 = 'Thread id: {} Delivery tag: {} Message body: {}'
        logger.info(fmt1.format(thread_id, delivery_tag, body))

        task_id = header_frame.headers.get("task_id")
        logger.info(
            ' [*] {0} Received task_id {1}. Executing...'.format(datetime.now(), task_id))

        consumer = "unknown"
        try:
            # import pdb; pdb.set_trace()
            consumer = method_frame.consumer_tag
            my_json = base64.b64decode(body).decode('utf8').replace("'", '"')
            json_data = json.loads(my_json)
            task_name = json_data.get('name')
            task_args = json_data.get('args')
            task_kwargs = json_data.get('kwargs')
            # 设定父任务环境变量，以防下次发送子任务的时候需要用到
            parent_options = {
                "id": task_id,
                "code": task_name
            }
            os.environ["SPARROW_TASK_PARENT_OPTIONS"] = str(parent_options)
            result = self.get_target_func(self.target_func_map[task_name])(*task_args, **task_kwargs)
            kwargs = {
                "status": "SUCCESS",
                "result": str(result) if result else '',
                "traceback": "",
            }
        except Exception as ex:
            kwargs = {
                "status": "FAILURE",
                "result": "",
                "traceback": ex.__str__()
            }
        if self.update_task:
            self.update_task_result(task_id, consumer, **kwargs)
        logger.info(
            ' [*] {0} Finished task_id {1}.'.format(datetime.now(), task_id))

        cb = functools.partial(self.ack_message, channel, delivery_tag)
        connection.add_callback_threadsafe(cb)

    def on_message(self, channel, method_frame, header_frame, body, args):
        (connection, threads) = args
        t = threading.Thread(target=self.do_work, args=(
            connection, channel, method_frame, header_frame, body))
        t.start()
        threads.append(t)

    def consume(self):
        # logger.info(' [*] QUEUE({}) Waiting for messages. To exit press CTRL+C'.format(self._queue))
        # # 建立连接
        while True:
            try:
                credentials = pika.PlainCredentials(
                    self._rabbitmq_user, self._rabbitmq_password)
                parameters = pika.ConnectionParameters(self._rabbitmq_addr,
                                                       self._rabbitmq_port,
                                                       '/',
                                                       credentials,
                                                       heartbeat=600)

                connection = pika.BlockingConnection(parameters)
                self._channel = connection.channel()
                logger.info(
                    ' [*] QUEUE({0}) Waiting for messages. To exit press CTRL+C'.format(self._queue))
                self._channel.basic_qos(prefetch_count=1)
                threads = []
                on_message_callback = functools.partial(
                    self.on_message, args=(connection, threads))
                self._channel.basic_consume(
                    queue=self._queue, on_message_callback=on_message_callback)
                self._channel.start_consuming()

                for thread in threads:
                    thread.join()
            # Don't recover if connection was closed by broker
            except pika.exceptions.ConnectionClosedByBroker:
                self._channel.stop_consuming()
                break
            # Don't recover on channel errors
            except pika.exceptions.AMQPChannelError:
                self._channel.stop_consuming()
                break
            # Recover on all other connection errors
            except BrokerConnectonException as ex:
                # raise Exception(ex.__repr__())
                logger.error(
                    "broker connection error:{0}. try again later".format(ex.__repr__()))
                time.sleep(2)
            except KeyboardInterrupt:
                self._channel.stop_consuming()

    def update_task_result(self, task_id, consumer, **kwargs):
        try:
            status = kwargs.get('status')
            data = {
                "task_id": task_id,
                "consumer": consumer,
                "status": status,
                "result": kwargs.get('result'),
                "traceback": kwargs.get('traceback'),
            }
            requests.post(self._task_api, data=data)
            logger.info(
                ' [*] Update task database info task_id is {0}, status is {1}'.format(task_id, status))
        except Exception as ex:
            raise Exception(ex.__repr__())