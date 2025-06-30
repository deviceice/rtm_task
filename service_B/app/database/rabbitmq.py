import os
from datetime import datetime

import aio_pika
from loguru import logger
from typing import Dict, Optional
from configparser import ConfigParser
from aiormq import AMQPError
from fastapi import HTTPException, Request
from service_B.app.models.schemas import TaskParameters


# Чтение конфига и формирование класса настроек обычно выноcим в отдельный модуль
class GetSettings:

    def __init__(self):
        self.config = ConfigParser()

    def open_conf(self):
        current_file_path = os.path.abspath(__file__)
        service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))
        conf_path = os.path.join(service_root, "config.ini")

        if not os.path.exists(conf_path):
            raise FileNotFoundError(f"Config file not found at: {conf_path}")

        with open(conf_path, 'r', encoding='utf-8') as config_file:
            self.config.read_file(config_file)

    def get_conf(self):
        return self.config


class SettingsRabbitmq:
    settings = GetSettings()
    settings.open_conf()
    config = settings.get_conf()
    USER_RABBITMQ = config['RABBITMQ']['user']
    PASS_RABBITMQ = config['RABBITMQ']['password']
    HOST_RABBITMQ = config['RABBITMQ']['host']
    PORT_RABBITMQ = int(config['RABBITMQ']['port'])


tasks_db: Dict[str, TaskParameters] = {}


class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        """Установка соединения с RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                host=SettingsRabbitmq.HOST_RABBITMQ,
                port=SettingsRabbitmq.PORT_RABBITMQ,
                login=SettingsRabbitmq.USER_RABBITMQ,
                password=SettingsRabbitmq.PASS_RABBITMQ
            )
            logger.success("Connected to RabbitMQ!")

            self.channel = await self.connection.channel()

            # Объявляем очереди
            await self.channel.declare_queue("configuration_tasks", durable=True)
            await self.channel.declare_queue("configuration_results", durable=True)

        except AMQPError as e:
            logger.critical(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def close(self):
        """Закрытие соединения с RabbitMQ"""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

    async def consume_results(self, tasks_db: dict):
        """Потребление результатов из очереди"""
        if not self.channel:
            return

        queue = await self.channel.get_queue("configuration_results")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    task_id = message.headers.get("task_id")
                    status = message.headers.get("status")

                    if task_id in tasks_db:
                        tasks_db[task_id].status = status
                        tasks_db[task_id].completed_at = datetime.now()


async def get_rabbitmq_client(request: Request):
    client = request.app.state.rabbitmq_client
    if not client or not client.channel:
        raise HTTPException(status_code=500, detail="RabbitMQ connection not available")
    return client
