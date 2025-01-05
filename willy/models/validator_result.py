from typing import List

from pydantic import BaseModel


class ValidatorResult(BaseModel):
    success: bool = False
    valid_instances: List = []
    invalid_instances: List = []
    message: str = ""
    verbose_message: str = ""
