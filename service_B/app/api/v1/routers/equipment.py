import re
import random
import aio_pika
import uuid

from datetime import datetime
from fastapi import APIRouter, Path, Depends

from service_B.app.database.rabbitmq import tasks_db, get_rabbitmq_client
from service_B.app.models.schemas import ConfigureResponseModel, ProvisionRequest, TaskParameters, StatusResponse

api_v1_equipment = APIRouter(
    prefix="/api/v1/equipment",
    tags=["equipment"],
    responses={404: {"description": "Not found"},
               500: {"descriptoon": "Internal provisioning exception"},
               }
)


@api_v1_equipment.post("/cpe/{id}",
                       response_model=ConfigureResponseModel,
                       summary="Конфигурация CPE устройства",
                       description="""t
    ### Настройка клиентского оборудования по серийному номеру
    - id: Серийный номер оборудования (6+ буквенно-цифровых символов)
    - timeoutInSeconds: Максимальное время выполнения операции (1-60 сек)
    - parameters: Параметры конфигурации устройства
    """,
                       # responses=response_examples, # Тут я добляю пример ответа для документации
                       )
async def configure_cpe(
        request: ProvisionRequest,
        id: str = Path(..., regex=r"^[a-zA-Z0-9]{6,}$", example="Ab12124"),
        rabbitmq_client=Depends(get_rabbitmq_client)

):
    if not re.fullmatch(r"Ab12124", id, re.IGNORECASE):
        return ConfigureResponseModel(code=404, message="The requested equipment is not found")

    if random.random() < 0.1:
        return ConfigureResponseModel(code=500, message="Internal provisioning exception")

    task_id = str(uuid.uuid4())

    task = TaskParameters(
        status="pending",
        equipment_id=id,
        task_id=task_id,
        parameters=request.parameters[0],
        created_at=datetime.now()
    )
    tasks_db[task_id] = task

    if rabbitmq_client:
        message = aio_pika.Message(
            body=task.json().encode(),
            headers={
                "task_id": task_id,
                "equipment_id": id
            }
        )
        await rabbitmq_client.channel.default_exchange.publish(
            message,
            routing_key="configuration_tasks"
        )

    return ConfigureResponseModel(
        code=200,
        message="Task created",
        taskId=task_id
    )


@api_v1_equipment.get("/api/v1/equipment/cpe/{id}/task/{task_id}",
                      response_model=StatusResponse,
                      summary="Проверка статуса задачи конфигурации")
async def check_task_status(
        id: str = Path(..., regex=r"^[a-zA-Z0-9]{6,}$", example="Ab12124"),
        task_id: str = Path(..., description="Уникальный ID задачи")
):
    # Проверка на существовании оборудования, как в ТЗ
    if not re.fullmatch(r"Ab12124", id, re.IGNORECASE):
        return StatusResponse(code=404, message="The requested equipment is not found")

    # Проверка на существование задачи как в ТЗ
    if task_id not in tasks_db:
        return StatusResponse(code=404, message="The requested task is not found")

    task = tasks_db[task_id]

    # Возвращаем статус задачи, как в ТЗ
    if task.status == "completed":
        return StatusResponse(code=200, message="Completed")
    elif task.status == "failed":
        return StatusResponse(code=500, message="Internal provisioning exception")
    else:
        return StatusResponse(code=204, message="Task is still running")
