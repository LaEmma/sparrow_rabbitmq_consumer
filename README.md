# Sparrow RabbitMQ Consumer


## Introduction
Sparrow rabbitmq consumer is a RabbitMQ (AMQP 0-9-1) client consumer library for Python.


* Python 3.5+ are supported.


## Documentation
pass

## Installation

```
pip install sparrow_rabbitmq_consumer
```

## Example

Here is the most simple example of use

```
from rabbitmq_consumer import RabbitMQConsumer

rabbitmq_config = {
    "NAME": "rabbitmq-svc"
    "HOST": "127.0.0.1",
    "PORT": "5672",
    "API_PORT": "15672",
    "USER": "admin",
    "PASSWORD": "12345",
    "VHOST": None
}

task_api_config = {
    "NAME": "sparrow-task-test-svc",
    "HOST": "127.0.0.1",
    "PORT": "8001",
    "UPDATE_TASK_API": '/api/sparrow_task/task/update/'
}


consumer = RabbitMQConsumer(
    queue="product", 
    rabbitmq_config=rabbitmq_config,
    update_task=True,
    task_api_config=task_api_config
)
consumer.consume()

参数说明：
    queue: rabbitmq队列名称
    rabbitmq_config: rabbitmq连接设置
    update_task: True/False    任务执行结束是否更新任务结果
    task_api_config: 如果update_task为True,则在任务执行完成之后会向该设置里的url发送任务执行完成结果

    rabbitmq_config和task_api_config为非必填，未设置的话会使用默认值，默认HOST均为127.0.0.1
    
    rabbitmq_config：
        {
            "NAME": "rabbitmq-svc"
            "HOST": "127.0.0.1",
            "PORT": "5672",
            "API_PORT": "15672",
            "USER": "admin",
            "PASSWORD": "12345",
            "VHOST": None
        }
        如果参数里传了NAME, 会把NAME作为rabbitmq服务的名称，以服务发现的方式获取HOST。
        如果服务发现未找到该服务则会使用参数里的HOST的值。
    
    task_api_config： 
        {
            "NAME": "sparrow-task-test-svc",
            "HOST": "127.0.0.1",
            "PORT": "8001",
            "UPDATE_TASK_API": '/api/sparrow_task/task/update/'
        }
        如果参数里传了NAME, 会把NAME作为task_api服务的名称，以服务发现的方式获取HOST。
        如果服务发现未找到该服务则会使用参数里的HOST的值。

    

```


