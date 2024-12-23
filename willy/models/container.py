from pydantic import BaseModel

from typing import List


class Container(BaseModel):
    cpu: int
    memory: int
    name: str
    ports_tcp: List[int] = []
    ports_udp: List[int] = []
    portMappings: List[dict[str, int]] = []

    @property
    def all_ports(self) -> List[int]:
        return self.ports_tcp + self.ports_udp


# with a gpu https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-gpu-specifying.html
