# -*- coding: utf-8 -*-
import os

# consul 地址
CONSUL_ADDR = {
    "HOST": os.environ.get("CONSUL_HOST", "127.0.0.1"),
    "PORT": os.environ.get("CONSUL_PORT", "8500")
}

RABBITMQ_BROKER = {
    "NAME": os.environ.get("RABBITMQ_SERVICE", None),
    "HOST": os.environ.get("RABBITMQ_SERVICE_HOST", "127.0.0.1"),
    "PORT": os.environ.get("RABBITMQ_SERVICE_PORT", "5672"),
    "API_PORT": os.environ.get("RABBITMQ_SERVICE_PORT", "15672"),
    "USER": os.environ.get("RABBITMQ_SERVICE_USER", "admin"),
    "PASSWORD": os.environ.get("RABBITMQ_SERVICE_PASSWORD", "s90jksdjksd34dsf"),
    "VHOST": os.environ.get("RABBITMQ_SERVICE_VHOST", None),
}

TASK_SERVICE ={
    "NAME": os.environ.get("TASK_SERVICE", None),
    "HOST": os.environ.get("TASK_SERVICE_HOST", "127.0.0.1"),
    "PORT": os.environ.get("TASK_SERVICE_PORT", "8001"),
    "UPDATE_TASK_API": '/api/sparrow_task/task/update/'
}


