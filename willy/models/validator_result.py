from pydantic import BaseModel
from typing import List


class ValidatorResult(BaseModel):
    success: bool = False
    valid_instances: List = []
    invalid_instances: List = []
    message: str = ""
    verbose_message: str = ""
