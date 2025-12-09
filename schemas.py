from pydantic import BaseModel,Field


class CalcRequest(BaseModel):
    operation: str = Field(..., description="Operation like add, subtract, multiply, divide, sqrt")
    operand1: float = Field(..., description="First number")
    operand2: float | None = Field(None, description="Second number (optional for sqrt)")


class CalcResponse(BaseModel):
    id: int
    operation: str
    operand1: float
    operand2: float | None
    result: float

    class Config:
        orm_mode = True
