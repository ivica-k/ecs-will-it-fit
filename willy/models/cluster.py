from typing import List, Optional

from pydantic import BaseModel

from .container_instance import ContainerInstance


class Cluster(BaseModel):
    name: str
    arn: str
    container_instances: Optional[List[ContainerInstance]] = []

    def _parse_dict(self):
        return Cluster(
            name=self["clusters"][0]["clusterName"],
            arn=self["clusters"][0]["clusterArn"],
        )

    @classmethod
    def parse_obj(cls, obj):
        try:
            return cls._parse_dict(obj)
        except IndexError as exc:
            cluster_arn = obj["failures"][0]["arn"]
            error_reason = obj["failures"][0]["reason"]

            print(f"Cluster '{cluster_arn}' does not exist. Reason: '{error_reason}.'")

    @property
    def cpu_total(self) -> int:
        cpu_total = 0

        for container_instance in self.container_instances:
            cpu_total += container_instance.cpu_total

        return cpu_total

    @property
    def cpu_remaining(self) -> int:
        cpu_remaining = 0

        for container_instance in self.container_instances:
            cpu_remaining += container_instance.cpu_remaining

        return cpu_remaining

    @property
    def memory_remaining(self) -> int:
        memory_remaining = 0

        for container_instance in self.container_instances:
            memory_remaining += container_instance.memory_remaining

        return memory_remaining

    @property
    def memory_total(self) -> int:
        memory_total = 0

        for container_instance in self.container_instances:
            memory_total += container_instance.memory_remaining

        return memory_total
