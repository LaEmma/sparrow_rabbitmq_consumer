# Sparrow RabbitMQ Consumer


## Introduction
Sparrow rabbitmq consumer is a RabbitMQ (AMQP 0-9-1) client consumer library for Python.


* Python 3.5+ are supported.

## Installation

```
pip install sparrow_rabbitmq_consumer
```

## Example

Here is the most simple example of use

```
from rabbitmq_consumer import RabbitMQConsumer

message_broker = "amqp://admin:12345@localhost:5672"
message_backend = "http://127.0.0.1:8001/api/sparrow_task/task/update/"

consumer = RabbitMQConsumer(
    queue="product", 
    message_broker=message_broker,
    message_backend=message_backend
)

# 需要定义queue中订阅的任务对应的执行函数
target_func_map = {
    "order_paid": "task.order_paid",
    "order_shipped": "task.order_shipped",
    "add_favorite": "task.add_favorite",
}
consumer.target_func_map = target_func_map
consumer.consume()

参数说明：
    queue: rabbitmq队列名称
    message_broker: rabbitmq连接设置
    message_backend: 选填的配置，如果设置了message_backend,则在任务执行完成之后会向该设置里的url发送任务执行完成结果

    在调用consumer.consume()之前需要给 target_func_map赋值，
    target_func_map字典中的键为message code，对应的值为执行该消息的任务函数路径字符串

```


