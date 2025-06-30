from typing import Optional, List

from pydantic import BaseModel, conint, Field


class Parameter(BaseModel):
    username: str
    password: str
    vlan: Optional[int] = None
    interfaces: Optional[List[int]] = None


class ProvisionRequest(BaseModel):
    timeoutInSeconds: conint(ge=1, le=60) = Field(..., description="Timeout between 1-60 seconds")
    parameters: List[Parameter] = Field(..., min_items=1, max_items=1)


class ResponseModel(BaseModel):
    code: int
    message: str
