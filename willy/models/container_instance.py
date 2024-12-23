from pydantic import BaseModel

from typing import List, Dict, Optional

from .attribute import Attribute


class ContainerInstance(BaseModel):
    arn: str
    instance_id: str
    cpu_remaining: int
    cpu_total: int
    memory_remaining: int
    memory_total: int
    attributes: List[Attribute]
    ports_tcp: Optional[List[int]] = []
    ports_udp: Optional[List[int]] = []

    class Config:
        frozen = True

    def __contains__(self, key):
        return key == self.arn

    def _parse_dict(self):
        container_instances = []

        for elem in self["containerInstances"]:
            container_instances.append(
                ContainerInstance(
                    arn=elem["containerInstanceArn"],
                    instance_id=elem["ec2InstanceId"],
                    cpu_total=elem["registeredResources"][0]["integerValue"],
                    cpu_remaining=elem["remainingResources"][0]["integerValue"],
                    memory_total=elem["registeredResources"][1]["integerValue"],
                    memory_remaining=elem["remainingResources"][1]["integerValue"],
                    attributes=elem["attributes"],
                    ports_tcp=elem["remainingResources"][2]["stringSetValue"],
                    ports_udp=elem["remainingResources"][3]["stringSetValue"],
                )
            )

        return container_instances

    @classmethod
    def parse_obj(cls, obj):
        return cls._parse_dict(obj)

    @property
    def all_ports(self) -> List:
        rez = self.ports_tcp + self.ports_udp
        return rez
