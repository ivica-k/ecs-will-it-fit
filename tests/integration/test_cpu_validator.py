import unittest

from parameterized import parameterized

from tests.helpers import (
    get_ecs_service,
    create_integration_test_resources,
    wait_until_service_stable,
    get_infra_config,
)
from willy.exceptions import NotEnoughCPUException
from willy.services.ecs_client import get_ecs_client
from willy.validators import CPUValidator


class TestCPUValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ecs_client = get_ecs_client()
        cls.cluster_name = "willy_cluster"
        cls.infra_config = get_infra_config()
        cls.subnets = (
            cls.infra_config.get("VPCStack").get("subnetprivateids").split(",")
        )

        cls.task_def_names = []
        cls.service_names = []

    @classmethod
    def tearDownClass(cls):
        for task_def in cls.task_def_names:
            cls.ecs_client.deregister_task_definition(taskDefinition=task_def)

        cls.ecs_client.delete_task_definitions(taskDefinitions=cls.task_def_names)

        for service in cls.service_names:
            cls.ecs_client.delete_service(
                cluster=cls.cluster_name, service=service, force=True
            )

    # t2.small has 1024 CPU units, 2GB memory
    @parameterized.expand(
        [
            ("service with one container on a cluster with more cpu", 256, 128, 1),
            ("service with two containers on a cluster with more cpu", 256, 128, 2),
            (
                "service with one container on a cluster with just enough cpu",
                1024,
                128,
                1,
            ),
            (
                "service with two containers on a cluster with just enough cpu",
                512,
                128,
                2,
            ),
        ]
    )
    def test_task_definition_fits(
        self, name, cpu_units: int, memory: int, desired_count: int
    ):
        service_name, task_def_name = create_integration_test_resources(
            name=name,
            ecs_client=self.ecs_client,
            cpu_units=cpu_units,
            memory=memory,
            desired_count=desired_count,
            subnets=self.subnets,
        )

        self.task_def_names.append(task_def_name)
        self.service_names.append(service_name)

        try:
            svc = get_ecs_service(
                cluster_name=self.cluster_name,
                ecs_client=self.ecs_client,
                service_name=service_name,
            )

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
                max_attempts=20,
            )

            desc_svc_response = self.ecs_client.describe_services(
                services=[svc.service.name], cluster=self.cluster_name
            )

            list_tasks_response = self.ecs_client.list_tasks(
                cluster=self.cluster_name,
                serviceName=service_name,
            )

            task_instance_arns = [
                elem.get("containerInstanceArn")
                for elem in self.ecs_client.describe_tasks(
                    cluster=self.cluster_name,
                    tasks=[list_tasks_response["taskArns"][0]],
                ).get("tasks")
            ]

            # validate that there is the same number of requested and running tasks and that there are no failures
            self.assertTrue(
                desc_svc_response.get("services")[0].get("runningCount")
                == desired_count
            )
            self.assertTrue((len(desc_svc_response.get("failures"))) == 0)

            self.assertTrue(service_stable)

            # stop running tasks to free up resources on the cluster before running CPUValidator;
            # if resources are taken by the running containers then CPUValidator results are skewed
            if service_stable:
                self.ecs_client.delete_service(
                    cluster=svc.cluster.name, service=service_name, force=True
                )

            # validate that the CPUValidator has the same result as the ECS scheduler - service can be scheduled
            result = CPUValidator().validate(
                service=svc.service,
                cluster=svc.cluster,
                container_instances=svc.cluster.container_instances,
            )

            self.assertTrue(result.success)
            self.assertTrue(len(result.valid_instances) > 0)

            # verify that there is at least 1 container instance on the cluster
            # that is also returned by the CPUValidator. This validates that the container is scheduled
            # on the same instance, therefore the CPUValidator works the same as the ECS scheduler
            validator_instance_arns = [elem.arn for elem in result.valid_instances]
            self.assertTrue(
                len(
                    [
                        elem
                        for elem in task_instance_arns
                        if elem in validator_instance_arns
                    ]
                )
                > 0
            )

        finally:
            # clean up if a test hits an exception
            self.ecs_client.delete_service(
                cluster=self.cluster_name, service=service_name, force=True
            )

    # t2.small has 1024 CPU units, 2GB memory
    @parameterized.expand(
        [
            (
                "service with one container on a cluster with less cpu",
                2048,
                128,
                1,
            ),  # none will fit cause 2048 > 1024
            (
                "service with three containers on a cluster with less cpu",
                1024,
                128,
                3,
            ),  # two will fit, third wont
        ]
    )
    def test_task_definition_doesnt_fit(
        self, name, cpu_units: int, memory: int, desired_count: int
    ):
        service_name, task_def_name = create_integration_test_resources(
            name=name,
            ecs_client=self.ecs_client,
            cpu_units=cpu_units,
            memory=memory,
            desired_count=desired_count,
            subnets=self.subnets,
        )

        self.task_def_names.append(task_def_name)
        self.service_names.append(service_name)

        try:
            svc = get_ecs_service(
                cluster_name=self.cluster_name,
                ecs_client=self.ecs_client,
                service_name=service_name,
            )

            # with get_ecs_service(cluster_name=self.cluster_name, ecs_client=self.ecs_client) as svc:

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
            )

            desc_svc_response = self.ecs_client.describe_services(
                services=[svc.service.name], cluster=self.cluster_name
            )

            # validate that the service is not running
            self.assertFalse(service_stable)

            # validate that there are fewer tasks running than desired; this happens when a container instance has
            # enough CPU for 1 container but the desired count is > 1
            self.assertTrue(
                desc_svc_response.get("services")[0].get("runningCount") < desired_count
            )

            # validate that the missing resource is CPU
            self.assertIn(
                "has insufficient CPU units available",
                desc_svc_response.get("services")[0].get("events")[0].get("message"),
            )

            # validate that the CPUValidator has the same result as the ECS scheduler - service can't be scheduled
            with self.assertRaises(NotEnoughCPUException):
                ().validate(
                    service=svc.service,
                    cluster=svc.cluster,
                    container_instances=svc.cluster.container_instances,
                )

            # clean up
            self.ecs_client.delete_service(
                cluster=svc.cluster.name, service=service_name, force=True
            )

        finally:
            # clean up if a test hits an exception
            self.ecs_client.delete_service(
                cluster=self.cluster_name, service=service_name, force=True
            )


if __name__ == "__main__":
    unittest.main()
