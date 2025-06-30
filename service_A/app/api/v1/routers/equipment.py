import asyncio
import re
import random

from fastapi import APIRouter, Path
from service_A.app.models.schemas import ResponseModel, ProvisionRequest

api_v1_equipment = APIRouter(
    prefix="/api/v1/equipment",
    tags=["equipment"],
    responses={404: {"description": "Not found"},
               500: {"descriptoon": "Internal provisioning exception"},
               }
)


@api_v1_equipment.post(
    "/cpe/{id}",
    response_model=ResponseModel,
    summary="Конфигурация CPE устройства",
    description="""t
    ### Настройка клиентского оборудования по серийному номеру
    - id: Серийный номер оборудования (6+ буквенно-цифровых символов)
    - timeoutInSeconds: Максимальное время выполнения операции (1-60 сек)
    - parameters: Параметры конфигурации устройства
    """,
    # responses=response_examples, # Добавить пример ответа для документации
)
async def configure_cpe(
        request: ProvisionRequest,
        id: str = Path(..., regex=r"^[a-zA-Z0-9]{6,}$", example="Ab12124"),

):
    # Пример использования в коде параметров
    params = request.parameters[0]
    username = params.username
    password = params.password
    vlan = params.vlan
    interfaces = params.interfaces

    # Эмуляция не найденного оборудования из ТЗ
    if not re.fullmatch(r"Ab12124", id, re.IGNORECASE):
        return ResponseModel(code=404, message="The requested equipment is not found")

    # Эмуляция случайной ошибки сервера 10% шанс ТЗ
    if random.random() < 0.3:
        return ResponseModel(code=500, message="Internal provisioning exception")

    # 60 сек ожидание перед ответом, сервис синхронный как указано в ТЗ
    await asyncio.sleep(60)
    return ResponseModel(code=200, message="success")
