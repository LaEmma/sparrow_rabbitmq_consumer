# -*- coding: utf-8 -*-
import os


RABBITMQ_BROKER = {
    "HOST": os.environ.get("RABBITMQ_SERVICE_HOST", "127.0.0.1"),
    "PORT": os.environ.get("RABBITMQ_SERVICE_PORT", "5672"),
    "API_PORT": os.environ.get("RABBITMQ_SERVICE_PORT", "15672"),
    "USER": os.environ.get("RABBITMQ_SERVICE_USER", "admin"),
    "PASSWORD": os.environ.get("RABBITMQ_SERVICE_PASSWORD", "s90jksdjksd34dsf"),
    "VHOST": os.environ.get("RABBITMQ_SERVICE_VHOST", None),
}

TASK_SERVICE ={
    "HOST": os.environ.get("TASK_SERVICE_HOST", "127.0.0.1"),
    "PORT": os.environ.get("TASK_SERVICE_PORT", "8001"),
    "UPDATE_TASK_API": '/api/sparrow_task/task/update/'
}


