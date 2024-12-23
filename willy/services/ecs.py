from willy.models import Cluster, TaskDefinition, ContainerInstance, Service
from typing import List
from sys import exit

import boto3


class ECSService:
    def __init__(
        self,
        ecs_client: boto3.Session.client,
        cluster_name: str,
        service_name: str,
    ):
        self.cluster_name = cluster_name
        self.service_name = service_name

        self.ecs_client = ecs_client

    def _get_cluster_info(self) -> Cluster:
        response = self.ecs_client.describe_clusters(clusters=[self.cluster_name])
        cluster: Cluster = Cluster.parse_obj(response)

        return cluster

    def _get_service_info(self) -> Service:
        response = self.ecs_client.describe_services(
            cluster=self.cluster_name, services=[self.service_name]
        )
        if len(response.get("services")) == 0:
            exit(f"Service named '{self.service_name}' doesn't exist.")

        service: Service = Service.parse_obj(response)

        task_def_response = self.ecs_client.describe_task_definition(
            taskDefinition=response["services"][0]["taskDefinition"]
        )
        task_definition: TaskDefinition = TaskDefinition.parse_obj(task_def_response)

        service.task_definition = task_definition

        return service

    def _get_instances_info(self) -> List[ContainerInstance]:
        container_instances: List = []

        instances = self.ecs_client.list_container_instances(
            cluster=self.cluster_name, status="ACTIVE"
        ).get("containerInstanceArns")

        if not instances:
            return container_instances

        response = self.ecs_client.describe_container_instances(
            cluster=self.cluster_name,
            containerInstances=instances,
        )

        for ci in response.get("containerInstances", []):
            container_instance = ContainerInstance(
                arn=ci.get("containerInstanceArn"),
                cpu_remaining=ci.get("remainingResources")[0].get("integerValue"),
                memory_remaining=ci.get("remainingResources")[1].get("integerValue"),
                cpu_total=ci.get("registeredResources")[0].get("integerValue"),
                memory_total=ci.get("registeredResources")[1].get("integerValue"),
                instance_id=ci.get("ec2InstanceId"),
                attributes=ci.get("attributes"),
            )

            container_instances.append(container_instance)

        return container_instances

    @property
    def cluster(self) -> Cluster:
        cluster = self._get_cluster_info()

        if cluster:
            cluster.container_instances = self._get_instances_info()

        return cluster

    @property
    def service(self) -> Service:
        return self._get_service_info()
