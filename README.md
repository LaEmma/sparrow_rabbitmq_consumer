# Sparrow RabbitMQ Consumer


## Introduction
Sparrow rabbitmq consumer is a RabbitMQ (AMQP 0-9-1) client consumer library for Python.


* Python 3.5+ are supported.


## Documentation
pass


## Example

Here is the most simple example of use

```
pip install sparrow_rabbitmq_consumer
from rabbitmq_consumer import RabbitMQConsumer
rabbitmq_config = {
    "HOST": "127.0.0.1",
    "PORT": "5672",
    "API_PORT": "15672",
    "USER": "admin",
    "PASSWORD": "12345",
    "VHOST": None
}
task_api = "http://127.0.0.1:8001/api/"
consumer = RabbitMQConsumer(
    queue="product", 
    task_file="task_folders.sparrow_products_tasks", 
    rabbitmq_config=rabbitmq_config,
    update_task=True,
    task_api=task_api
)
consumer.consume()

```