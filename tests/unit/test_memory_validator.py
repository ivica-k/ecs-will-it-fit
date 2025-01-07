import unittest

from parameterized import parameterized

from tests.helpers import (
    get_service,
    get_task_definition,
    get_cluster,
)
from willy.exceptions import NotEnoughMemoryException
from willy.models import Cluster, TaskDefinition, Service
from willy.validators import MemoryValidator


class TestMemoryValidator(unittest.TestCase):
    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, 512, 256),
            ("one node two containers one replica", 1, 2, 1, 512, 200),
            ("one node two containers two replicas", 1, 2, 2, 1024, 200),
            ("two nodes one container one replica", 2, 1, 1, 512, 256),
            ("two nodes two containers one replica", 2, 2, 1, 512, 128),
            ("two nodes two containers two replicas", 2, 2, 2, 1024, 128),
        ]
    )
    def test_service_fits_on_a_cluster_with_more_memory(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        memory_node: int,
        memory_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=128, memory=memory_node, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128, memory=memory_container, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        result = MemoryValidator().validate(
            service=service,
            cluster=cluster,
            container_instances=cluster.container_instances,
        )

        self.assertTrue(result.success)

    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, 512, 512),
            ("one node two containers one replica", 1, 2, 1, 512, 256),
            ("one node two containers two replicas", 1, 2, 2, 1024, 256),
            ("two nodes one container one replica", 2, 1, 1, 512, 512),
            ("two nodes two containers one replica", 2, 2, 1, 512, 256),
            ("two nodes two containers two replicas", 2, 2, 2, 1024, 256),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with_equal_memory(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        memory_node: int,
        memory_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=128, memory=memory_node, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128, memory=memory_container, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(NotEnoughMemoryException):
            MemoryValidator().validate(
                service=service,
                cluster=cluster,
                container_instances=cluster.container_instances,
            )

    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, 256, 512),
            ("one node two containers one replica", 1, 2, 1, 256, 256),
            ("one node two containers two replicas", 1, 2, 2, 256, 256),
            ("two nodes one container one replica", 2, 1, 1, 256, 512),
            ("two nodes two containers one replica", 2, 2, 1, 128, 256),
            ("two nodes two containers two replicas", 2, 2, 2, 128, 256),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with_less_memory(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        memory_node: int,
        memory_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=128, memory=memory_node, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128, memory=memory_container, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(NotEnoughMemoryException):
            MemoryValidator().validate(
                service=service,
                cluster=cluster,
                container_instances=cluster.container_instances,
            )
