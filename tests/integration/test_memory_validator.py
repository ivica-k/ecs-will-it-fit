import unittest

from parameterized import parameterized


from willy.validators import MemoryValidator
from willy.exceptions import NotEnoughMemoryException
from tests.helpers import (
    get_ecs_service,
    create_integration_test_resources,
    wait_until_service_stable,
    wait_until_service_inactive,
    get_infra_config,
)
from willy.services.ecs_client import get_ecs_client


class TestMemoryValidator(unittest.TestCase):
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

    # t2.small has 1024 CPU units, 2GB memory (1978MB available)
    @parameterized.expand(
        [
            ("service with one container on a cluster with more memory", 256, 128, 1),
            ("service with two containers on a cluster with more memory", 256, 512, 2),
            (
                "service with one container on a cluster with just enough memory",
                256,
                1978,
                1,
            ),
            (
                "service with two containers on a cluster with just enough memory",
                256,
                1978,
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

            # stop running tasks to free up resources on the cluster before running MemoryValidator;
            # if resources are taken by the running containers then MemoryValidator results are skewed
            if service_stable:
                self.ecs_client.delete_service(
                    cluster=svc.cluster.name, service=service_name, force=True
                )

                wait_until_service_inactive(
                    ecs_client=self.ecs_client,
                    service_name=svc.service.name,
                    max_attempts=20,
                )  # give ECS time to free up resources after a service is deleted

            # validate that the MemoryValidator has the same result as the ECS scheduler - service can be scheduled
            result = MemoryValidator(
                service=svc.service, cluster=svc.cluster
            ).validate()

            self.assertTrue(result.success)
            self.assertTrue(len(result.valid_instances) > 0)

            # verify that there is at least 1 container instance on the cluster
            # that is also returned by the MemoryValidator. This validates that the container is scheduled
            # on the same instance, therefore the MemoryValidator works the same as the ECS scheduler
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

    # # t2.small has 1024 CPU units, 2GB memory
    @parameterized.expand(
        [
            ("service with one container on a cluster with less memory", 256, 2048, 1),
            ("service with 3 containers on a cluster with less memory", 256, 1024, 3),
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

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
                max_attempts=20,
            )

            desc_svc_response = self.ecs_client.describe_services(
                services=[svc.service.name], cluster=self.cluster_name
            )

            # validate that the service is not running
            self.assertFalse(service_stable)

            # validate that there are fewer tasks running than desired; this happens when a container instance has
            # enough memory for 1 container but the desired count is > 1
            self.assertTrue(
                desc_svc_response.get("services")[0].get("runningCount") < desired_count
            )

            # validate that the missing resource is memory
            self.assertIn(
                "has insufficient memory available",
                desc_svc_response.get("services")[0].get("events")[0].get("message"),
            )

            # validate that the MemoryValidator has the same result as the ECS scheduler - service can't be scheduled
            with self.assertRaises(NotEnoughMemoryException):
                MemoryValidator(service=svc.service, cluster=svc.cluster).validate()

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
