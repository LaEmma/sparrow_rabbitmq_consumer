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
import requests

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

    def __init__(self, queue, task_file, rabbitmq_config=None, update_task=True, task_api_config=None):
        """
        输入参数说明：
        queue:  定义consumer所在队列
        task_file: 总任务文件的名称
        rabbitmq_config: rabbitmq链接配置。不传则使用默认
        update_task: 是否在执行完更新task数据库
        task_api_config: 如果需要更新task数据库，则需要传入更新接口。不传则使用默认
        """
        # 检查queue的定义，已经queue是否已经存在在broker中
        if not rabbitmq_config:
            rabbitmq = RABBITMQ_BROKER
            logger.info("rabbitmq_config not defined, use default setting: {0}".format(RABBITMQ_BROKER))
        else:
            if not isinstance(rabbitmq_config, dict):
                raise Exception("rabbitmq_config is not type of dict")
            rabbitmq = RABBITMQ_BROKER
            for key, value in rabbitmq_config.items():
                rabbitmq[key] = value 

        if not queue:
            raise Exception("queue is not defined")
        # 检查总的task py 文件是否存在
        if not task_file:
            raise Exception("task_file is not defined")
        try:
            self._task_module = importlib.import_module(task_file)
        except:
            raise Exception(
                "cannot locate task_file: {}".format(task_file))
        self.update_task = update_task
        if self.update_task:
            task_service = TASK_SERVICE
            if task_api_config:
                for key, value in task_api_config.items():
                    task_service[key] = value
            else:
                logger.info("task_api not defined, use default api: {0}".format(task_api))
        self._task_api = get_task_api(task_service)
        self.rabbitmq_url(rabbitmq)
        # 检查queue的定义，已经queue是否已经存在在broker中
        if not self.validate_queue(queue):
            raise Exception(
                "queue {} is not defined in rabbitmq broker".format(queue))
        self._queue = queue

    def get_task_api(task_api_config):
        task_url = get_service_addr(TASK_SERVICE)
        task_api = "http://{0}{1}".format(task_url, TASK_SERVICE['UPDATE_TASK_API'])
        return task_api


    def rabbitmq_url(self, rabbitmq_config):
        # import pdb; pdb.set_trace()
        try:
            rabbitmq_url = get_service_addr(rabbitmq_config)
            addr = rabbitmq_url.split(':')[0]
            port = rabbitmq_url.split(':')[1]
            # addr = rabbitmq_config['HOST']
            # port = rabbitmq_config['PORT']
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

    def callback(self, ch, method, properties, body):
        task_id = properties.headers.get("task_id")
        logger.info(' [*] Received task_id {}. Executing...'.format(task_id))

        try:
            my_json = base64.b64decode(body).decode('utf8').replace("'", '"')
            json_data = json.loads(my_json)
            task_name = json_data.get('name')
            task_parameter = json_data.get('parameter')

            consumer = method.consumer_tag
            if task_parameter:
                result = getattr(self._task_module, task_name)(task_parameter)
            else:
                result = getattr(self._task_module, task_name)()
            kwargs = {
                "status": "SUCCESS",
                "result": result,
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
        logger.info(' [*] Finished task_id {}.'.format(task_id))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume(self):
        # logger.info(' [*] QUEUE({}) Waiting for messages. To exit press CTRL+C'.format(self._queue))
        # 建立连接
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.URLParameters(self._connection_url))
                self._channel = connection.channel()
                logger.info(
                    ' [*] QUEUE({}) Waiting for messages. To exit press CTRL+C'.format(self._queue))
                self._channel.basic_qos(prefetch_count=1)
                self._channel.basic_consume(
                    queue=self._queue,
                    auto_ack=True,  # 如果设为False,任务正确执行完成之后才会ack
                    on_message_callback=self.callback,)
                self._channel.start_consuming()
            # Don't recover if connection was closed by broker
            except pika.exceptions.ConnectionClosedByBroker:
                break
            # Don't recover on channel errors
            except pika.exceptions.AMQPChannelError:
                break
            # Recover on all other connection errors
            except BrokerConnectonException as ex:
                raise Exception(ex.__repr__())

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
