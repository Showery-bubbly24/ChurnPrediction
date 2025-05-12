from pydantic import BaseModel
from typing import List


class Request(BaseModel):
    gender: str
    age: int
    tenure: int
    partner: int
    dependents: int
    services: List[str]
    contract: str
    paperless_billing: int
    payment_method: str
    monthlyCharges: float
