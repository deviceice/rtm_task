import asyncio
import aio_pika
import aiohttp
import json

from loguru import logger
from datetime import datetime
from typing import Dict

from service_B.app.database.rabbitmq import SettingsRabbitmq

API_BASE_URL = "http://localhost:8001"  # URL FastAPI Server_A


class TaskProcessor:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.session = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=SettingsRabbitmq.HOST_RABBITMQ,
            port=SettingsRabbitmq.PORT_RABBITMQ,
            login=SettingsRabbitmq.USER_RABBITMQ,
            password=SettingsRabbitmq.PASS_RABBITMQ
        )
        self.channel = await self.connection.channel()
        self.session = aiohttp.ClientSession(base_url=API_BASE_URL)
        logger.success("Connected to RabbitMQ and created HTTP session")

    async def close(self):
        if self.session:
            await self.session.close()
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.success("Connections closed")

    async def process_task(self, task_data: Dict):
        task_id = task_data["task_id"]
        equipment_id = task_data["equipment_id"]

        try:
            async with self.session.post(
                    f"/api/v1/equipment/cpe/{equipment_id}",
                    json={
                        "parameters": [task_data["parameters"]],
                        "timeoutInSeconds": 60
                    }
            ) as response:
                result = await response.json()

                await self.send_result(
                    task_id=task_id,
                    status="completed" if result["code"] == 200 else "failed",
                    result=result
                )

        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            await self.send_result(
                task_id=task_id,
                status="failed",
                result={"error": str(e)}
            )

    async def send_result(self, task_id: str, status: str, result: Dict):
        message = aio_pika.Message(
            body=json.dumps(result).encode(),
            headers={
                "task_id": task_id,
                "status": status,
                "processed_at": datetime.now().isoformat()
            }
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key="configuration_results"
        )
        logger.info(f"Result for task {task_id} sent to queue")

    async def consume_tasks(self):
        queue = await self.channel.declare_queue(
            "configuration_tasks",
            durable=True
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        task_data = json.loads(message.body.decode())
                        logger.info(f"Processing task: {task_data['task_id']}")
                        asyncio.create_task(self.process_task(task_data))

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")


async def main():
    processor = TaskProcessor()
    try:
        await processor.connect()
        await processor.consume_tasks()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())
