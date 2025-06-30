from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, conint, Field


class Parameter(BaseModel):
    username: str
    password: str
    vlan: int
    interfaces: List[int]


class ProvisionRequest(BaseModel):
    timeoutInSeconds: conint(ge=1, le=60) = Field(..., description="Timeout between 1-60 seconds")
    parameters: List[Parameter] = Field(..., min_items=1, max_items=1)


class ConfigureResponseModel(BaseModel):
    code: int
    message: str
    taskId: Optional[str] = None


class StatusResponse(BaseModel):
    code: int
    message: str


class TaskParameters(BaseModel):
    status: str
    equipment_id: str
    task_id: str
    parameters: Parameter
    created_at: datetime
    completed_at: Optional[datetime] = None
