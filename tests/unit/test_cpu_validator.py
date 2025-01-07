import unittest

from parameterized import parameterized

from tests.helpers import (
    get_service,
    get_cluster,
    get_task_definition,
)
from willy.exceptions import NotEnoughCPUException
from willy.models import Cluster, Service, TaskDefinition
from willy.validators import CPUValidator


class TestCPUValidator(unittest.TestCase):
    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, 512, 256),
            ("one node two containers one replica", 1, 2, 1, 512, 256),
            ("one node two containers two replicas", 1, 2, 2, 1024, 256),
            ("two nodes one container one replica", 2, 1, 1, 512, 256),
            ("two nodes two containers one replica", 2, 2, 1, 512, 256),
            ("two nodes two containers two replicas", 2, 2, 2, 1024, 128),
        ]
    )
    def test_service_fits_on_a_cluster_with_more_cpu(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        cpu_node: int,
        cpu_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=cpu_node, memory=8192, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=cpu_container, memory=512, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )

        result = CPUValidator().validate(
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
            ("two nodes two containers one replica", 2, 2, 1, 1024, 512),
            ("two nodes two containers two replicas", 2, 2, 2, 1024, 256),
        ]
    )
    def test_service_fits_on_a_cluster_with_just_enough_cpu(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        cpu_node: int,
        cpu_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=cpu_node, memory=8192, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=cpu_container, memory=512, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        result = CPUValidator().validate(
            service=service,
            cluster=cluster,
            container_instances=cluster.container_instances,
        )

        self.assertTrue(result.success)

    @parameterized.expand(
        [
            ("one node one container one replica", 1, 1, 1, 512, 1024),
            ("one node two containers one replica", 1, 2, 1, 512, 512),
            ("one node two containers two replicas", 1, 2, 2, 1024, 512),
            ("two nodes one container one replica", 2, 1, 1, 512, 768),
            ("two nodes two containers one replica", 2, 2, 1, 1024, 768),
            ("two nodes two containers two replicas", 2, 2, 2, 1024, 768),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with_less_cpu(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        cpu_node: int,
        cpu_container: int,
    ):
        cluster: Cluster = get_cluster(
            cpu=cpu_node, memory=8192, attributes=[], ports=[], num_nodes=num_nodes
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=cpu_container, memory=512, num_containers=num_containers
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(NotEnoughCPUException):
            CPUValidator().validate(
                service=service,
                cluster=cluster,
                container_instances=cluster.container_instances,
            )
