import json
from typing import List, Dict, Union
from uuid import uuid4

from botocore.exceptions import WaiterError

from willy.models import TaskDefinition, Cluster, ContainerInstance, Service, Container
from willy.services import ECSService


def read_json(file_path: str) -> dict:
    with open(file_path, "r") as input_data:
        return json.loads(input_data.read())


def get_task_definition_from_json(file_path: str) -> TaskDefinition:
    return TaskDefinition.parse_obj(read_json(file_path))


def get_task_definition(
    cpu: int = 512,
    memory: int = 512,
    num_containers: int = 1,
    ports_tcp: list = None,
    ports_udp: list = None,
    requires_attributes: List[Dict[str, str]] = [],
    placement_constraints: Union[List, None] = None,
) -> TaskDefinition:
    if not requires_attributes:
        requires_attributes = []

    if not placement_constraints:
        placement_constraints = []

    if not ports_tcp:
        ports_tcp = []

    if not ports_udp:
        ports_udp = []

    containers = [
        Container(
            cpu=cpu,
            memory=memory,
            name="container",
            ports_tcp=ports_tcp,
            ports_udp=ports_udp,
        ).model_dump()
        for _ in range(num_containers)
    ]

    task_definition: TaskDefinition = TaskDefinition(
        name="task_def",
        arn="arn:aws:ecs:eu",
        containers=containers,
        requires_attributes=requires_attributes,
        placement_constraints=placement_constraints,
        # ports=[],
    )
    # taskdef = {
    #     "taskDefinition": {
    #         "taskDefinitionArn": "arn:aws:ecs:eu/abc:123",
    #         "containerDefinitions": containers,
    #         # "family": "one-replica-subnet-matches-512-512",
    #         "networkMode": "awsvpc",
    #         "revision": 26,
    #         "volumes": [],
    #         "status": "ACTIVE",
    #         "requiresAttributes": requires_attributes,
    #         "placementConstraints": placement_constraints,
    #         "compatibilities": ["EC2"],
    #         "cpu": f"{cpu}",
    #         "memory": f"{memory}",
    #         "registeredAt": "2024-12-13T20:02:01.733Z",
    #         "registeredBy": "arn:aws:iam::932785857088:user/ikolenkas",
    #         "tags": [],
    #     }
    # }

    # task_definition: TaskDefinition = TaskDefinition.parse_obj(taskdef)

    return task_definition


def get_cluster(
    cpu: int = 512,
    memory: int = 512,
    num_nodes: int = 1,
    attributes: list = None,
    ports: List[int] = None,
) -> Cluster:
    if not attributes:
        attributes = []

    if not ports:
        ports = []

    instances = [
        ContainerInstance(
            arn="arn:aws:ecs:eu-west-1:123456789012:container-instance/cluster-prod/47dcb64f",
            cpu_remaining=cpu,
            cpu_total=8192,
            memory_remaining=memory,
            memory_total=15742,
            attributes=attributes,
            instance_id="abc-111",
            ports_tcp=ports,
        )
        for _ in range(num_nodes)
    ]

    return Cluster(
        name="cluster-prod",
        arn="arn:aws:ecs:eu-west-1:123456789012:cluster/cluster-prod",
        container_instances=instances,
    )


def get_service(task_definition: TaskDefinition, desired_count: int = 1) -> Service:
    return Service(
        name="test_service",
        arn="arn:aws:ecs:eu",
        desired_count=desired_count,
        task_definition=task_definition,
    )


def get_ecs_service(cluster_name: str, ecs_client, service_name: str) -> ECSService:
    return ECSService(
        cluster_name=cluster_name,
        ecs_client=ecs_client,
        service_name=service_name,
    )


# class get_ecs_service():
#     def __init__(self, cluster_name: str, ecs_client, service_name: str):
#         self.cluster_name = cluster_name
#         self.ecs_client = ecs_client
#         self.service_name = service_name
#
#     def __enter__(self) -> ECSService:
#
#         return ECSService(
#             cluster_name=self.cluster_name,
#             ecs_client=self.ecs_client,
#             service_name=self.service_name,
#         )
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         return None


def run_task(ecs_client, service: Service, cluster: Cluster, infra_config: dict):
    return ecs_client.run_task(
        cluster=cluster.name,
        taskDefinition=service.task_definition.name,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [
                    infra_config.get("VPCStack").get("subnetprivateid"),
                ],
                "securityGroups": [],
                "assignPublicIp": "DISABLED",
            }
        },
    )


def register_task_definition(
    ecs_client,
    family: str,
    cpu: int,
    memory: int,
    placement_constraints: Union[List, None] = None,
) -> str:
    if not placement_constraints:
        placement_constraints = []

    response = ecs_client.register_task_definition(
        networkMode="awsvpc",
        containerDefinitions=[
            {
                "name": "app",
                "image": "nginx:latest",
                "links": [],
                "portMappings": [
                    {"containerPort": 8125, "hostPort": 8125, "protocol": "udp"},
                    {"containerPort": 8080, "hostPort": 8080, "protocol": "tcp"},
                ],
                "essential": True,
                "entryPoint": [],
                "command": [],
            }
        ],
        family=family,
        memory=f"{memory}",
        cpu=f"{cpu}",
        placementConstraints=placement_constraints,
    )

    return f'{response["taskDefinition"]["family"]}:{response["taskDefinition"]["revision"]}'


def create_ecs_service(
    ecs_client,
    service_name: str,
    task_def_name: str,
    desired_count: int,
    subnets: List,
    placement_constraints: Union[List, None] = None,
):
    if not placement_constraints:
        placement_constraints = []

    ecs_client.create_service(
        cluster="willy_cluster",
        serviceName=service_name,
        desiredCount=desired_count,
        taskDefinition=task_def_name,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": [],
                "assignPublicIp": "DISABLED",
            },
        },
        placementConstraints=placement_constraints,
    )


def create_integration_test_resources(
    name,
    ecs_client,
    desired_count,
    subnets,
    cpu_units=512,
    memory=512,
    placement_constraints: Union[List, None] = None,
):
    random_string = uuid4().hex[:4]
    task_def_name = name.replace(" ", "-")
    service_name = f"{name}-{random_string}".replace(" ", "-")

    # create taskdef
    task_def_name_revision = register_task_definition(
        ecs_client=ecs_client,
        family=f"{task_def_name}-{cpu_units}-{memory}",
        cpu=cpu_units,
        memory=memory,
        placement_constraints=placement_constraints,
    )

    create_ecs_service(
        ecs_client=ecs_client,
        desired_count=desired_count,
        service_name=service_name,
        subnets=subnets,
        task_def_name=f"{task_def_name}-{cpu_units}-{memory}",
        placement_constraints=placement_constraints,
    )

    return service_name, task_def_name_revision


class create_integration_test_resources_context:
    def __init__(
        self,
        name,
        ecs_client,
        desired_count,
        subnets,
        cpu_units,
        memory,
        placement_constraints,
    ):
        self.name = name
        self.ecs_client = ecs_client
        self.desired_count = desired_count
        self.subnets = subnets
        self.cpu_units = cpu_units
        self.memory = memory
        self.placement_constraints = placement_constraints

    def __enter__(self) -> ECSService:
        random_string = uuid4().hex[:4]
        task_def_name = self.name.replace(" ", "-")
        service_name = f"{self.name}-{random_string}".replace(" ", "-")

        # create taskdef
        task_def_name_revision = register_task_definition(
            ecs_client=self.ecs_client,
            family=f"{task_def_name}-{self.cpu_units}-{self.memory}",
            cpu=self.cpu_units,
            memory=self.memory,
            placement_constraints=self.placement_constraints,
        )

        create_ecs_service(
            ecs_client=self.ecs_client,
            desired_count=self.desired_count,
            service_name=service_name,
            subnets=self.subnets,
            task_def_name=f"{task_def_name}-{self.cpu_units}-{self.memory}",
            placement_constraints=self.placement_constraints,
        )

        return service_name, task_def_name_revision


def get_infra_config():
    with open("./infra/out.json") as input_file:
        return json.load(input_file)


def wait_until_service_stable(
    ecs_client, service_name: str, max_attempts: int = 10
) -> bool:
    infra_config = get_infra_config()

    cluster_name = infra_config.get("ECSStack").get("ClusterName")

    try:
        ecs_client.get_waiter("services_stable").wait(
            cluster=cluster_name,
            services=[service_name],
            WaiterConfig={"Delay": 10, "MaxAttempts": max_attempts},
        )

        return True

    except WaiterError:
        return False


def wait_until_service_inactive(
    ecs_client, service_name: str, max_attempts: int = 10
) -> bool:
    infra_config = get_infra_config()

    cluster_name = infra_config.get("ECSStack").get("ClusterName")

    try:
        ecs_client.get_waiter("services_inactive").wait(
            cluster=cluster_name,
            services=[service_name],
            WaiterConfig={"Delay": 10, "MaxAttempts": max_attempts},
        )

        return True

    except WaiterError:
        return False
