# -*- coding: utf-8 -*-
import consul
from .rabbitmq_config import *


def get_service_addr(service_conf, scheme="http"):
    """
        先尝试用consul获取服务地址，如未获取到则使用HOST和POST
    """
    port = ""
    host = ""
    service_addr = "{host}:{port}"
    service_env_host = service_conf['HOST']
    service_env_port = service_conf['PORT']
    service_name = service_conf['NAME']

    if service_name:
        # 使用 consul 服务发现
        consul_client_addr = CONSUL_ADDR
        consul_client = consul.Consul(
            host=consul_client_addr['HOST'],
            port=consul_client_addr['PORT'],
            scheme=scheme
        )
        try:
            port = consul_client.catalog.service(service_name)[1][0]['ServicePort']
            host = consul_client.catalog.service(service_name)[1][0]['ServiceAddress']
            print("consul服务发现地址：服务名称{0},host{1},port{2}".format(service_name, host, port))
        except Exception as ex:
            # 获取环境变量
            host = service_env_host
            port = service_env_port
            print("consul未找到服务，使用参数地址。服务名称{0},host{1},port{2}".format(service_name, host, port))
    else:
        # 获取环境变量
        host = service_env_host
        port = service_env_port
        print("未配置服务名称，使用参数地址。host{0},port{1}".format(host, port))
    service_addr = service_addr.format(host=host, port=port)
    return service_addr
