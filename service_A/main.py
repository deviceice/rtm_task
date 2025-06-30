import uvicorn

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from service_A.app.api.v1.routers.equipment import api_v1_equipment
from service_A.app.models.tags_api import tags_metadata

app = FastAPI(title="Service_A",
              debug=True,
              version="0.1",
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
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
