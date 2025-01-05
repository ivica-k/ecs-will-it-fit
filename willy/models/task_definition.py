from typing import List, Optional

from pydantic import BaseModel

from .attribute import Attribute
from .container import Container


def _port_range_to_range(port_range: str):
    start, end = port_range.split("-")
    start = int(start)
    end = int(end)

    return range(int(start), int(end) + 1)


def _parse_ports(container: dict) -> (List[int], List[int]):
    ports_tcp = []
    ports_udp = []

    for mapping in container.get("portMappings"):  # TODO: this can also be a range
        if mapping.get("protocol") == "tcp":
            try:
                ports_tcp.append(int(mapping["hostPort"]))
            except KeyError:
                ports_tcp.extend(
                    [
                        elem
                        for elem in _port_range_to_range(mapping["containerPortRange"])
                    ]
                )
        elif mapping.get("protocol") == "udp":
            try:
                ports_udp.append(int(mapping["hostPort"]))
            except KeyError:
                ports_udp.extend(
                    [
                        elem
                        for elem in _port_range_to_range(mapping["containerPortRange"])
                    ]
                )

    return ports_tcp, ports_udp


class TaskDefinition(BaseModel):
    name: str
    arn: str
    containers: List[Container]
    cpu: int = 0
    memory: int = 0
    placement_constraints: Optional[List[Attribute]]
    # compatibilities: List
    requires_attributes: Optional[List[Attribute]]
    # ports: List[int] = []

    # For containers in a task with the awsvpc network mode, the hostPortRange is set to the same value as the
    # containerPortRange. This is a static mapping strategy.
    #
    # For containers in a task with the bridge network mode, the Amazon ECS agent finds open host ports from the default
    # ephemeral range and passes it to docker to bind them to the container ports.

    def _parse_dict(self):
        containers = []
        cpu = self.get("taskDefinition").get("cpu", 0)
        memory = self.get("taskDefinition").get("memory", 0)

        for cont in self["taskDefinition"]["containerDefinitions"]:
            ports_tcp, ports_udp = _parse_ports(cont)

            container: Container = Container(
                cpu=cont.get("cpu", 0),
                memory=cont.get("memory", 0),
                name=cont.get("name"),
                ports_tcp=ports_tcp,
                ports_udp=ports_udp,
            )

            containers.append(container)

        try:
            attributes = [
                Attribute.parse_obj(elem)
                for elem in self["taskDefinition"]["requiresAttributes"]
            ]

            attributes_from_constraints = []

            for constraint in self["taskDefinition"]["placementConstraints"]:
                if "[" in constraint.get("expression") and "]" in constraint.get(
                    "expression"
                ):
                    attributes_from_constraints.extend(
                        Attribute.parse_multiple(constraint.get("expression"))
                    )
                else:
                    attributes_from_constraints.append(Attribute.parse_obj(constraint))

            # found_attributes = attributes + attributes_from_constraints
            attributes.extend(
                attr for attr in attributes_from_constraints if attr not in attributes
            )

        except KeyError:
            found_attributes = []

        return TaskDefinition(
            name=self["taskDefinition"]["taskDefinitionArn"].split("/")[1],
            arn=self["taskDefinition"]["taskDefinitionArn"],
            containers=containers,
            requires_attributes=attributes,
            placement_constraints=attributes_from_constraints,
            ports=[elem.all_ports for elem in containers][0],
            cpu=cpu,
            memory=memory,
        )

    @classmethod
    def parse_obj(cls, obj):
        return cls._parse_dict(obj)

    @property
    def total_cpu_needed(self) -> int:
        cpu_needed = 0

        for container in self.containers:
            cpu_needed += container.cpu

        return max(self.cpu, cpu_needed)

    @property
    def total_memory_needed(self) -> int:
        memory_needed = 0

        for container in self.containers:
            memory_needed += container.memory

        return max(self.memory, memory_needed)

    @property
    def all_ports(self) -> List[int]:
        all_ports = []

        for container in self.containers:
            all_ports += container.all_ports

        return list(set(all_ports))
