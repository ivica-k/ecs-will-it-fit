import unittest

from tests.constants import just_enough_attributes, all_attributes
from tests.helpers import get_cluster, get_service, get_task_definition
from willy.exceptions import MissingECSAttributeException
from willy.models import TaskDefinition, Cluster, Service, Attribute
from willy.validators import AttributesValidator


from parameterized import parameterized


class TestAttributesValidator(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "one node one container one replica just enough attributes",
                1,
                1,
                1,
                just_enough_attributes,
                just_enough_attributes,
            ),
            (
                "one node two containers one replica all attributes",
                1,
                2,
                1,
                all_attributes,
                all_attributes,
            ),
            (
                "one node two containers two replicas docker api version equal",
                1,
                2,
                2,
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
            ),
            (
                "one node two containers two replicas docker api version higher",
                2,
                2,
                2,
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.31"}],
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
            ),
            (
                "one node two containers two replicas docker api version higher more cluster attrs",
                2,
                2,
                2,
                [
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.31"},
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.20"},
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.25"},
                ],
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
            ),
        ]
    )
    def test_service_fits_on_a_cluster_with(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        cluster_attributes: list,
        task_def_attributes: list,
    ):
        cluster: Cluster = get_cluster(
            cpu=128,
            memory=128,
            attributes=cluster_attributes,
            ports=[],
            num_nodes=num_nodes,
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            requires_attributes=task_def_attributes,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        result = AttributesValidator(service=service, cluster=cluster).validate()

        self.assertTrue(result.success)

    @parameterized.expand(
        [
            (
                "one node two containers two replicas docker api version lower",
                1,
                2,
                2,
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.15"}],
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
            ),
            (
                "one node two containers two replicas attribute missing",
                1,
                2,
                2,
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
                [
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
                    {"name": "com.amazonaws.ecs.capability.ecr-auth"},
                ],
            ),
            (
                "one node two containers two replicas docker api one version missing",
                1,
                2,
                2,
                [{"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"}],
                [
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.20"},
                ],
            ),
            (
                "one node two containers two replicas docker api one version lower",
                1,
                2,
                2,
                [
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.20"},
                ],
                [
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
                    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.21"},
                ],
            ),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with(
        self,
        name: str,
        num_nodes: int,
        num_containers: int,
        desired_count: int,
        cluster_attributes: list,
        task_def_attributes: list,
    ):
        cluster: Cluster = get_cluster(
            cpu=128,
            memory=128,
            attributes=cluster_attributes,
            ports=[],
            num_nodes=num_nodes,
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            requires_attributes=task_def_attributes,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(MissingECSAttributeException):
            AttributesValidator(service=service, cluster=cluster).validate()

    @parameterized.expand(
        [
            (
                "one node one container one replica all builtin attributes are valid",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.vpc-id", "value": "vpc-04c4656e20f1ff7e7"},
                    {"name": "ecs.instance-type", "value": "t2.small"},
                    {"name": "ecs.subnet-id", "value": "subnet-0a1710c3328d7ecd1"},
                    {"name": "ecs.ami-id", "value": "ami-06d198da422b4d577"},
                    {"name": "ecs.availability-zone", "value": "eu-central-1a"},
                    {"name": "ecs.os-type", "value": "linux"},
                    {"name": "ecs.os-family", "value": "LINUX"},
                    {"name": "ecs.cpu-architecture", "value": "x86_64"},
                    {"name": "ecs.capability.external"},
                    {
                        "name": "ecs.awsvpc-trunk-id",
                        "value": "a6148e89-0416-415d-97e0-f23d18e134a4",
                    },
                ],  # built-in attributes https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-placement-constraints.html#attributes
            ),
        ]
    )
    def test_service_fits_on_a_cluster_with_builtin_attributes(
        self,
        name: str,
        desired_count: int,
        num_nodes: int,
        num_containers: int,
        cluster_attributes: list,
        task_def_attributes: list,
    ):
        cluster: Cluster = get_cluster(
            cpu=128,
            memory=128,
            attributes=cluster_attributes,
            ports=[],
            num_nodes=num_nodes,
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            requires_attributes=task_def_attributes,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        result = AttributesValidator(service=service, cluster=cluster).validate()

        self.assertTrue(result.success)

    @parameterized.expand(
        [
            (
                "one node one container one replica wrong vpc id",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.vpc-id", "value": "vpc-abcd"},
                ],
            ),
            (
                "one node one container one replica wrong instance type",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.instance-type", "value": "t2.malisa"},
                ],
            ),
            (
                "one node one container one replica wrong subnet id",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.subnet-id", "value": "subnet-abcd"},
                ],
            ),
            (
                "one node one container one replica wrong AMI id",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.ami-id", "value": "ami-abcd"},
                ],
            ),
            (
                "one node one container one replica wrong AZ",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.availability-zone", "value": "eu-decentral-1a"},
                ],
            ),
            (
                "one node one container one replica wrong OS type",
                1,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.os-type", "value": "pingu"},
                ],
            ),
            (
                "one node one container two replica wrong OS family",
                1,
                1,
                2,
                all_attributes,
                [
                    {"name": "ecs.os-family", "value": "PINGUS"},
                ],
            ),
            (
                "one node three container one replica wrong CPU architecture",
                1,
                3,
                1,
                all_attributes,
                [
                    {"name": "ecs.cpu-architecture", "value": "powerpc"},
                ],
            ),
            (
                "three node one container one replica wrong trunk id",
                3,
                1,
                1,
                all_attributes,
                [
                    {"name": "ecs.awsvpc-trunk-id", "value": "abcd"},
                ],
            ),
            (
                "one node one container three replica wrong ECS capability",
                1,
                1,
                3,
                all_attributes,
                [
                    {"name": "ecs.capability.internal"},
                ],
            ),
            (
                "one node two container one replica wrong AZ wrong CPU architecture",
                1,
                2,
                1,
                all_attributes,
                [
                    {"name": "ecs.availability-zone", "value": "eu-decentral-1a"},
                    {"name": "ecs.cpu-architecture", "value": "powerpc"},
                ],
            ),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with_builtin_attributes(
        self,
        name: str,
        desired_count: int,
        num_nodes: int,
        num_containers: int,
        cluster_attributes: list,
        task_def_attributes: list,
    ):
        cluster: Cluster = get_cluster(
            cpu=128,
            memory=128,
            attributes=cluster_attributes,
            ports=[],
            num_nodes=num_nodes,
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            requires_attributes=task_def_attributes,
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(MissingECSAttributeException) as context:
            AttributesValidator(service=service, cluster=cluster).validate()

        verbose_exception = context.exception.verbose_message
        attribute_names = [elem.get("name") for elem in task_def_attributes]

        # assert that the attribute is included in the verbose message shown to the user
        for attr_name in attribute_names:
            self.assertIn(attr_name, verbose_exception)

    @parameterized.expand(
        [
            (
                "one node one container one replica wrong vpc id",
                1,
                1,
                1,
                all_attributes,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.instance-type==t2.nano",
                    }
                ],  # instance-type in the cluster is t2.small,
            ),
            (
                "one node one container one replica wrong instance type",
                1,
                1,
                1,
                all_attributes,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.subnet-id in [subnet-12345, subnet-abcdef]",
                    }
                ],  # non-existing subnets,
            ),
            (
                "one node one container one replica api version doesnt exist",
                1,
                1,
                1,
                all_attributes,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:com.amazonaws.ecs.capability.docker-remote-api.9.31 exists",
                    }
                ],  # 1.44 is the latest as of 2024-12-12
            ),
        ]
    )
    def test_service_does_not_fit_on_a_cluster_with_builtin_attributes_placement_constraints(
        self,
        name: str,
        desired_count: int,
        num_nodes: int,
        num_containers: int,
        cluster_attributes: list,
        placement_constraints: list,
    ):
        cluster: Cluster = get_cluster(
            cpu=128,
            memory=128,
            attributes=cluster_attributes,
            ports=[],
            num_nodes=num_nodes,
        )
        task_definition: TaskDefinition = get_task_definition(
            cpu=128,
            memory=128,
            num_containers=num_containers,
            requires_attributes=[],
            placement_constraints=[
                Attribute.parse_obj(elem) for elem in placement_constraints
            ],
        )
        service: Service = get_service(
            desired_count=desired_count, task_definition=task_definition
        )
        service.task_definition = task_definition

        with self.assertRaises(MissingECSAttributeException) as context:
            AttributesValidator(service=service, cluster=cluster).validate()

        verbose_exception = context.exception.verbose_message
        attribute_names = [
            Attribute.parse_obj(elem).name for elem in placement_constraints
        ]

        # assert that all attributes are included in the verbose message shown to the user
        for attr_name in attribute_names:
            self.assertIn(attr_name, verbose_exception)


# ovde dodaj test koji priverava da je instance-type g4dn.xlarge i moras taj atribut staviti na cluster
# dodaj test koji proverava da li ima dovoljno gpuova, tu moras container instance model promeniti
