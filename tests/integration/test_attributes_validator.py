import unittest
from copy import copy

from parameterized import parameterized

from tests.helpers import (
    get_ecs_service,
    create_integration_test_resources,
    wait_until_service_stable,
    get_infra_config,
)
from willy.exceptions import MissingECSAttributeException
from willy.services.ecs_client import get_ecs_client
from willy.validators import AttributesValidator


class TestAttributesValidator(unittest.TestCase):
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
        cls.attributes = []

    @classmethod
    def tearDownClass(cls):
        for task_def in cls.task_def_names:
            cls.ecs_client.deregister_task_definition(taskDefinition=task_def)

        cls.ecs_client.delete_task_definitions(taskDefinitions=cls.task_def_names)

        if cls.attributes:
            for attr in cls.attributes:
                cls.ecs_client.delete_attributes(
                    cluster=cls.cluster_name, attributes=[attr]
                )

        for service in cls.service_names:
            cls.ecs_client.delete_service(
                cluster=cls.cluster_name, service=service, force=True
            )

    @parameterized.expand(
        [
            (
                "one replica one attribute",
                1,
                [
                    {
                        "name": "my_attribute",
                        "value": "awsome",
                        "targetType": "container-instance",
                    }
                ],
                [{"type": "memberOf", "expression": "attribute:my_attribute==awsome"}],
            ),
            (
                "one replica two attributes",
                1,
                [
                    {
                        "name": "my_attribute",
                        "value": "awsome",
                        "targetType": "container-instance",
                    },
                    {
                        "name": "my_2nd_attribute",
                        "value": "awsome2",
                        "targetType": "container-instance",
                    },
                ],
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:my_attribute==awsome",
                    },
                    {
                        "type": "memberOf",
                        "expression": "attribute:my_2nd_attribute==awsome2",
                    },
                ],
            ),
        ]
    )
    def test_service_fits_on_a_cluster_with_custom_attributes(
        self,
        name: str,
        desired_count: int,
        cluster_attributes: list,
        placement_constraints: list,
    ):
        service_name, task_def_name = create_integration_test_resources(
            name=name,
            ecs_client=self.ecs_client,
            cpu_units=512,
            memory=512,
            desired_count=desired_count,
            subnets=self.subnets,
            placement_constraints=placement_constraints,
        )

        self.task_def_names.append(task_def_name)
        self.service_names.append(service_name)

        try:
            svc = get_ecs_service(
                cluster_name=self.cluster_name,
                ecs_client=self.ecs_client,
                service_name=service_name,
            )

            # set attributes on container instances
            for attribute in cluster_attributes:
                for instance in svc.cluster.container_instances:
                    attribute["targetId"] = instance.arn

                    # used when deleting attributes from instances
                    attr_without_value = copy(attribute)
                    del attr_without_value["value"]
                    del attr_without_value["targetType"]
                    attr_without_value["targetId"] = instance.arn

                    self.attributes.append(attr_without_value)

                    self.ecs_client.put_attributes(
                        cluster=self.cluster_name,
                        attributes=[attribute],
                    )

            instance_filter = " && ".join(
                [elem.get("expression") for elem in placement_constraints]
            )

            instances_with_attribute = (
                get_ecs_client()
                .list_container_instances(
                    cluster=self.cluster_name, filter=instance_filter, status="ACTIVE"
                )
                .get("containerInstanceArns")
            )

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
                max_attempts=20,
            )

            self.assertTrue(service_stable)

            # assert that the number of instances with the attribute(s) is the same as total number of instances
            self.assertEqual(
                len(instances_with_attribute), len(svc.cluster.container_instances)
            )

            result = AttributesValidator().validate(
                service=svc.service,
                cluster=svc.cluster,
                container_instances=svc.cluster.container_instances,
            )

            self.assertTrue(result.success)
            self.assertEqual(len(instances_with_attribute), len(result.valid_instances))

        finally:
            # clean up if a test hits an exception
            self.ecs_client.delete_service(
                cluster=self.cluster_name, service=service_name, force=True
            )

    @parameterized.expand(
        [
            (
                "one replica docker api version exists",
                1,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:com.amazonaws.ecs.capability.docker-remote-api.1.31 exists",
                    }
                ],  # 1.17 and 1.44 at time of writing
            ),
            (
                "one replica subnet matches",
                1,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.subnet-id in SUBNETS_PLACEHOLDER",
                    }
                ],
            ),
            (
                "two replicas ec2 instance type matches",
                2,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.instance-type==t2.small",
                    }
                ],
            ),
        ]
    )
    def test_service_fits_on_a_cluster_with_builtin_attributes(  # TODO: implement as unit tests also
        self,
        name: str,
        desired_count: int,
        placement_constraints: list,
    ):
        if "subnet-id" in placement_constraints[0].get("expression", {}):
            placement_constraints[0]["expression"] = (
                placement_constraints[0]
                .get("expression")
                .replace("SUBNETS_PLACEHOLDER", str(self.subnets))
            )

        service_name, task_def_name = create_integration_test_resources(
            name=name,
            ecs_client=self.ecs_client,
            cpu_units=512,
            memory=512,
            desired_count=desired_count,
            subnets=self.subnets,
            placement_constraints=placement_constraints,
        )

        self.task_def_names.append(task_def_name)
        self.service_names.append(service_name)

        try:
            svc = get_ecs_service(
                cluster_name=self.cluster_name,
                ecs_client=self.ecs_client,
                service_name=service_name,
            )

            instance_filter = " && ".join(
                [elem.get("expression") for elem in placement_constraints]
            )

            instances_with_attribute = (
                get_ecs_client()
                .list_container_instances(
                    cluster=self.cluster_name, filter=instance_filter, status="ACTIVE"
                )
                .get("containerInstanceArns")
            )

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
                max_attempts=20,
            )

            self.assertTrue(service_stable)

            # assert that the number of instances with the attribute(s) is the same as total number of instances
            self.assertEqual(
                len(instances_with_attribute), len(svc.cluster.container_instances)
            )

            result = AttributesValidator().validate(
                service=svc.service,
                cluster=svc.cluster,
                container_instances=svc.cluster.container_instances,
            )

            self.assertTrue(result.success)
            self.assertEqual(len(instances_with_attribute), len(result.valid_instances))

        finally:
            # clean up if a test hits an exception
            self.ecs_client.delete_service(
                cluster=self.cluster_name, service=service_name, force=True
            )

    @parameterized.expand(
        [
            (
                "one replica docker api version doesnt exist",
                1,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:com.amazonaws.ecs.capability.docker-remote-api.9.31 exists",
                    }
                ],  # 1.44 is the latest as of 2024-12-12
            ),
            (
                "one replica wrong subnets",
                1,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.subnet-id in [subnet-12345, subnet-abcdef]",
                    }
                ],  # non-existing subnets
            ),
            (
                "two replicas wrong ec2 instance type",
                2,
                [
                    {
                        "type": "memberOf",
                        "expression": "attribute:ecs.instance-type==t2.nano",
                    }
                ],  # instance-type in the cluster is t2.small
            ),
        ]
    )  # builtin attributes are those attributes assigned by ECS by default
    def test_service_doesnt_fit_on_a_cluster_with_wrong_builtin_attributes(
        self,
        name: str,
        desired_count: int,
        placement_constraints: list,
    ):
        service_name, task_def_name = create_integration_test_resources(
            name=name,
            ecs_client=self.ecs_client,
            cpu_units=512,
            memory=512,
            desired_count=desired_count,
            subnets=self.subnets,
            placement_constraints=placement_constraints,
        )

        self.task_def_names.append(task_def_name)
        self.service_names.append(service_name)

        try:
            svc = get_ecs_service(
                cluster_name=self.cluster_name,
                ecs_client=self.ecs_client,
                service_name=service_name,
            )

            instance_filter = " && ".join(
                [elem.get("expression") for elem in placement_constraints]
            )

            instances_with_attribute = (
                get_ecs_client()
                .list_container_instances(
                    cluster=self.cluster_name, filter=instance_filter, status="ACTIVE"
                )
                .get("containerInstanceArns")
            )

            service_stable = wait_until_service_stable(
                ecs_client=self.ecs_client,
                service_name=svc.service.name,
            )

            desc_svc_response = self.ecs_client.describe_services(
                services=[svc.service.name], cluster=self.cluster_name
            )

            # validate that the service is not stable
            self.assertFalse(service_stable)

            self.assertTrue(
                desc_svc_response.get("services")[0].get("runningCount") < desired_count
            )

            # validate that the attribute used in the placement constrain is missing
            self.assertIn(
                "MemberOf placement constraint unsatisfied",
                desc_svc_response.get("services")[0].get("events")[0].get("message"),
            )

            # assert that the number of instances with the attribute(s) is 0
            self.assertEqual(len(instances_with_attribute), 0)

            with self.assertRaises(MissingECSAttributeException) as context:
                AttributesValidator().validate(
                    service=svc.service,
                    cluster=svc.cluster,
                    container_instances=svc.cluster.container_instances,
                )

            verbose_exception = context.exception.verbose_message
            attribute_name = instance_filter.replace("attribute:", "").split()[0]

            # assert that the placement constraint attribute is included in the verbose message shown to the user
            self.assertIn(attribute_name, verbose_exception)

        finally:
            # clean up if a test hits an exception
            self.ecs_client.delete_service(
                cluster=self.cluster_name, service=service_name, force=True
            )
