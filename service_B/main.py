import asyncio
import uvicorn

from loguru import logger
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from service_B.app.api.v1.routers.equipment import api_v1_equipment
from service_B.app.models.tags_api import tags_metadata
from service_B.app.database.rabbitmq import RabbitMQClient, tasks_db


async def lifespan(app: FastAPI):
    rabbitmq_client = RabbitMQClient()
    try:
        await rabbitmq_client.connect()
        app.state.rabbitmq_client = rabbitmq_client
        asyncio.create_task(rabbitmq_client.consume_results(tasks_db))
        yield
    except Exception as e:
        logger.error(f"Не удалось подключиться к rabbitmq  {e}")
    finally:
        await rabbitmq_client.close()
        logger.success("Работа сервера завершена!")


app = FastAPI(title="Service_B",
              debug=True,
              version="0.1",
              lifespan=lifespan,
              openapi_tags=tags_metadata
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


app.include_router(api_v1_equipment)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
