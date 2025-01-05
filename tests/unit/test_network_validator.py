import unittest
from typing import List

from parameterized import parameterized

from tests.helpers import (
    get_cluster,
    get_service,
    get_task_definition,
    get_task_definition_from_json,
)
from willy.exceptions import NoPortsAvailableException
from willy.models import TaskDefinition, Cluster, Service
from willy.validators import NetworkValidator


class TestNetworkValidator(unittest.TestCase):
    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, [22], [8080], [8081]),
            (
                "one node one container one replica tcp range",
                1,
                1,
                1,
                [22],
                [8080, 9000],
                [8081],
            ),
            (
                "one node one container one replica udp range",
                1,
                1,
                1,
                [22],
                [8080],
                [8081, 9000],
            ),
            (
                "one node one container one replica node port range",
                1,
                1,
                1,
                [22, 53, 80],
                [8080, 9000],
                [8081, 8082],
            ),
            (
                "one node two containers one replica",
                1,
                2,
                1,
                [22, 53],
                [8080, 8081],
                [8080, 8081],
            ),
            (
                "one node two containers two replicas",
                1,
                2,
                2,
                [22],
                [8080, 8081, 3000],
                [8080, 8081, 3000],
            ),
            ("two nodes one container one replica", 2, 1, 1, [22, 53], [21], [21]),
            (
                "two nodes two containers one replica",
                2,
                2,
                1,
                [21, 22, 53],
                [3000, 5000],
                [3000, 5000],
            ),
            (
                "two nodes two containers two replicas",
                2,
                2,
                2,
                [21, 22, 53],
                [3000, 5000, 8080],
                [3000, 5000, 8080],
            ),
        ]
    )
    def test_service_with_a_port_fits_on_a_cluster_with_that_port_free(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        ports_node: List[int],
        ports_tcp: List[int],
        ports_udp: List[int],
    ):
        cluster: Cluster = get_cluster(
            cpu=128, memory=128, attributes=[], ports=ports_node, num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            ports_tcp=ports_tcp,
            ports_udp=ports_udp,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        result = NetworkValidator(service=service, cluster=cluster).validate()

        self.assertTrue(result.success)

    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, [22], [22], [8081]),
            (
                "one node one container one replica node port range",
                1,
                1,
                1,
                [22, 53],
                [53],
                [8081],
            ),
            (
                "one node one container one replica tcp range",
                1,
                1,
                1,
                [22, 53],
                [53, 80],
                [8081],
            ),
            (
                "one node one container one replica udp range",
                1,
                1,
                1,
                [22, 53],
                [80],
                [8081, 22],
            ),
            (
                "one node two containers one replica",
                1,
                2,
                1,
                [22, 53],
                [8080, 8081],
                [8080, 53],
            ),
            (
                "one node two containers two replicas",
                1,
                2,
                2,
                [22],
                [8080, 8081, 3000],
                [8080, 22, 3000],
            ),
            ("two nodes one container one replica", 2, 1, 1, [22, 53], [22], [21]),
            (
                "two nodes two containers one replica",
                2,
                2,
                1,
                [21, 22, 53],
                [3000, 53],
                [3000, 5000],
            ),
            (
                "two nodes two containers two replicas",
                2,
                2,
                2,
                [21, 22, 53],
                [3000, 5000, 8080],
                [22, 5000, 8080],
            ),
        ]
    )
    def test_service_with_a_port_does_not_fit_on_a_cluster_with_that_port_used(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        ports_node: List[int],
        ports_tcp: List[int],
        ports_udp: List[int],
    ):
        cluster: Cluster = get_cluster(
            cpu=128, memory=128, attributes=[], ports=ports_node, num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            ports_tcp=ports_tcp,
            ports_udp=ports_udp,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(NoPortsAvailableException):
            NetworkValidator(service=service, cluster=cluster).validate()

    def test_task_def_with_port_range_produces_a_valid_model(self):
        # task definition has two containers; one has TCP ports set as range 80-85 and
        # the other container has UDP ports set as range 8000-8001
        task_definition: TaskDefinition = get_task_definition_from_json(
            "tests/assets/port_range_task_definition.json"
        )

        ports_tcp = [80, 81, 82, 83, 84, 85]
        ports_udp = [8000, 8001]
        all_ports = ports_tcp + ports_udp

        self.assertTrue(len(task_definition.containers) == 2)
        self.assertTrue(task_definition.containers[0].ports_tcp == ports_tcp)
        self.assertTrue(task_definition.containers[0].all_ports == ports_tcp)
        self.assertTrue(task_definition.containers[1].all_ports == ports_udp)
        self.assertTrue(task_definition.containers[1].ports_udp == ports_udp)

        self.assertTrue(task_definition.all_ports.sort() == all_ports.sort())
