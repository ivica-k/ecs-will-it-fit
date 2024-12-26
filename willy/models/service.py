from typing import List, Dict, Optional

from pydantic import BaseModel

from .attribute import Attribute
from .task_definition import TaskDefinition


class Service(BaseModel):
    name: str
    arn: str
    task_definition: Optional[TaskDefinition] = None
    desired_count: int = 1
    # requires_attributes: Optional[List[Dict[str, str]]]
    # placement_constraints: Optional[List[Dict[str, str]]]
    # placement_strategy: Optional[List[Dict[str, str]]]


    def _parse_dict(self):
        _service = self["services"][0]

        return Service(
            name=_service["serviceName"],
            arn=_service["serviceArn"],
            desired_count=_service["desiredCount"],
        )

    @classmethod
    def parse_obj(cls, obj):
        return cls._parse_dict(obj)

    @property
    def total_cpu_needed(self) -> int:
        return (
            self.task_definition.total_cpu_needed * self.desired_count
            if self.task_definition
            else 0
        )

    @property
    def total_memory_needed(self) -> int:
        return (
            self.task_definition.total_memory_needed * self.desired_count
            if self.task_definition
            else 0
        )

    @property
    def all_ports(self) -> List[int]:
        return self.task_definition.all_ports if self.task_definition else []

    @property
    def requires_attributes(self) -> List[Attribute]:
        return self.task_definition.requires_attributes if self.task_definition.requires_attributes else self.task_definition.placement_constraints

        # return (
        #     self.task_definition.requires_attributes
        #     # + self.task_definition.placement_constraints
        #     if self.task_definition
        #     else self.requires_attributes
        # )
