import unittest
from typing import List

from parameterized import parameterized

from tests.helpers import read_json
from willy.models import TaskDefinition, _port_range_to_range, _parse_ports


class TestTaskDefinitionModel(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "one container",
                read_json("tests/assets/task_definition.json"),
            ),
            (
                "multi container",
                read_json("tests/assets/multi_container_task_def.json"),
            ),
            (
                "multi container port range",
                read_json("tests/assets/port_range_task_definition.json"),
            ),
        ]
    )
    def test_taskdef_model_from_json(self, name: str, task_def_json):
        task_def = task_def_json.get("taskDefinition")
        task_def_model: TaskDefinition = TaskDefinition.parse_obj(task_def_json)
        container_memory = 0
        container_cpu = 0

        attributes_json = [
            # only 'name' is read from the attribute model to easily compare them with dictionaries below
            {"name": elem.model_dump(exclude_none=True).get("name")}
            for elem in task_def_model.requires_attributes
        ]

        for container in task_def.get("containerDefinitions"):
            container_memory += container.get("memory")
            container_cpu += container.get("cpu")

        self.assertEqual(
            task_def_model.name, f"{task_def.get('family')}:{task_def.get('revision')}"
        )
        self.assertEqual(task_def_model.total_cpu_needed, container_cpu)
        self.assertEqual(task_def_model.total_memory_needed, container_memory)
        self.assertEqual(attributes_json, task_def.get("requiresAttributes"))
        self.assertEqual(
            len(task_def_model.containers), len(task_def.get("containerDefinitions"))
        )

    @parameterized.expand(
        [
            (
                "8000-8080",
                "8000-8080",
                range(8000, 8081),
            ),  # second argument is up-to, not including
            (
                "22-22",
                "22-22",
                range(22, 23),
            ),  # second argument is up-to, not including
        ]
    )
    def test_port_range_to_range(
        self, name: str, port_range: str, expected_range: range
    ):
        actual_range = _port_range_to_range(port_range)

        self.assertEqual(actual_range, expected_range)

    @parameterized.expand(
        [
            (
                "one container",
                read_json("tests/assets/task_definition.json")
                .get("taskDefinition")
                .get("containerDefinitions"),
                [8080, 8085],
                [],
            ),
            (
                "multi container",
                read_json("tests/assets/multi_container_task_def.json")
                .get("taskDefinition")
                .get("containerDefinitions"),
                [8080],
                [],
            ),
            (
                "multi container port range",
                read_json("tests/assets/port_range_task_definition.json")
                .get("taskDefinition")
                .get("containerDefinitions"),
                [80, 81, 82, 83, 84, 85],
                [8000, 8001],
            ),
        ]
    )
    def test_parse_ports(
        self,
        name: str,
        containers: List[dict],
        expected_tcp: List[int],
        expected_udp: List[int],
    ):
        for container in containers:
            tcp, udp = _parse_ports(container)

            # skip containers without ports
            if tcp:
                self.assertEqual(tcp, expected_tcp)
            if udp:
                self.assertEqual(udp, expected_udp)
