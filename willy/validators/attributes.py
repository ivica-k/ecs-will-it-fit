import re
from typing import List

from willy.exceptions import MissingECSAttributeException
from willy.models import (
    Cluster,
    ValidatorResult,
    ContainerInstance,
    Service,
    Attribute,
)

VERSION_REGEX = r"(.*?)(\d\.\d{1,})"
SQUARE_BRACKETS_REGEX = r"[\[\]]"


def _split_attr_version(attribute_name: str):
    return re.search(VERSION_REGEX, attribute_name).groups()


def _contains_version(attribute_name: str):
    return bool(re.match(VERSION_REGEX, attribute_name))


def _contains_square_brackets(attribute_name: str):
    return bool(re.search(SQUARE_BRACKETS_REGEX, attribute_name))


def _compare_versioned_attribute(
    task_def_attributes: List[Attribute], container_instance_attributes: List[Attribute]
):
    lesser_than_or_equal_to_required = []
    greater_than_or_equal_to_required = []

    for task_def_attribute in task_def_attributes:
        attribute_name, task_def_version = _split_attr_version(task_def_attribute.name)

        relevant_ci_attrs = [
            Attribute(name=elem.name)
            for elem in container_instance_attributes
            if elem.name.startswith(attribute_name)
        ]

        # if com.amazonaws.ecs.capability.docker-remote-api.1.19 is in attributes on the container instance with the
        # same version
        if task_def_attribute in relevant_ci_attrs:
            lesser_than_or_equal_to_required.append(task_def_attribute)

        # if not, we have to compare versions
        else:
            for attr in relevant_ci_attrs:
                _, instance_attribute_version = _split_attr_version(attr.name)
                # python compares strings lexicographically, so
                # com.amazonaws.ecs.capability.docker-remote-api.1.19 > com.amazonaws.ecs.capability.docker-remote-api.1.18
                if task_def_version > instance_attribute_version:
                    greater_than_or_equal_to_required.append(task_def_attribute)
                else:
                    # com.amazonaws.ecs.capability.docker-remote-api.1.19 < com.amazonaws.ecs.capability.docker-remote-api.1.20
                    lesser_than_or_equal_to_required.append(task_def_attribute)

    if not lesser_than_or_equal_to_required and not greater_than_or_equal_to_required:
        return False

    # if the list of attributes with version lesser than or equal to the one on container instances is equal to the list of task def attributes
    # then the container instance has all the attributes that the task def requires
    return sorted(list(set(lesser_than_or_equal_to_required))) == sorted(
        [Attribute(name=elem.name) for elem in task_def_attributes]
    )


def _split_attributes(attributes: List[Attribute]):
    versioned_attributes = []
    non_versioned_attributes = []
    # subnets, AZs look like attribute:ecs.availability-zone in [us-east-1a, us-east-1b]
    list_attributes = []

    for attr in attributes:
        if _contains_version(attr.name):
            versioned_attributes.append(attr)
        elif attr.raw and _contains_square_brackets(attr.raw):
            list_attributes.extend(Attribute.parse_multiple(attr.raw))
        else:
            non_versioned_attributes.append(attr)

    return versioned_attributes, non_versioned_attributes, list_attributes


class AttributesValidator:
    def __init__(self, service: Service, cluster: Cluster):
        self.service: Service = service
        self.cluster: Cluster = cluster

        self.missing_attributes = []
        self.result: ValidatorResult = ValidatorResult()

    def _raise_exception(self):
        missing_attrs_str = f"""{f"{chr(10)}".join([str(elem) for elem in list(set(self.missing_attributes))])}"""

        self.result.verbose_message = (
            f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
            f"There are no container instances that have the attributes required by the task definition.\nMissing "
            f"attribute(s):\n\n{missing_attrs_str}"
        )

        self.result.message = (
            f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
            f"There are no container instances that have the attributes required by the task definition."
        )

        raise MissingECSAttributeException(
            message=self.result.message,
            verbose_message=self.result.verbose_message,
            valid_instances=self.result.valid_instances,
            invalid_instances=self.result.invalid_instances,
        )

    def _validate_versioned_attributes(
        self,
        versioned_attributes: List[Attribute],
        container_instances: List[ContainerInstance],
    ) -> List[ContainerInstance]:
        valid_instances = []

        for container_instance in container_instances:
            versioned_instance_attributes, _, _ = _split_attributes(
                container_instance.attributes
            )
            all_attributes_present = sorted(
                versioned_attributes, key=lambda attr: attr.name
            ) == sorted(versioned_instance_attributes, key=lambda attr: attr.name)

            if all_attributes_present:
                valid_instances.append(container_instance)
            else:
                all_attribute_greater_than_or_equal_to = _compare_versioned_attribute(
                    task_def_attributes=versioned_attributes,
                    container_instance_attributes=container_instance.attributes,
                )

                if all_attribute_greater_than_or_equal_to:
                    valid_instances.append(container_instance)
                else:
                    self.missing_attributes.extend(versioned_attributes)

        return valid_instances

    def _validate_list_attributes(
        self,
        list_attributes: List[Attribute],
        container_instances: List[ContainerInstance],
    ):
        valid_instances = []

        def attribute_on_instance(
            attribute: Attribute, container_instance: ContainerInstance
        ):
            attribute.raw = None
            return bool(attribute in container_instance.attributes)

        for container_instance in container_instances:
            for attr in list_attributes:
                if attribute_on_instance(attr, container_instance):
                    valid_instances.append(container_instance)
                else:
                    self.missing_attributes.append(attr)

        return valid_instances

    def _validate_non_versioned_attributes(
        self,
        non_versioned_attributes: List[Attribute],
        container_instances: List[ContainerInstance],
    ):
        valid_instances = []

        for container_instance in container_instances:
            # there's a chance that the list of attributes on the task def and the container instance are equal,
            # in which case the instance is considered valid.
            if (
                self.service.task_definition.requires_attributes
                == container_instance.attributes
            ):
                valid_instances.append(container_instance)

            else:
                for attr in non_versioned_attributes:
                    if attr not in container_instance.attributes:
                        self.missing_attributes.append(attr)

            if len(self.missing_attributes) > 0:
                self.result.invalid_instances.append(
                    {
                        "arn": container_instance.arn,
                        "reason": f"Missing attributes: {', '.join([elem.name for elem in self.missing_attributes])}",
                    }
                )

                # remove the current instance from the list of all valid instances by matching the ARN
                # this happens when an instance has one valid versioned attribute and one invalid non-versioned attribute
                self.result.valid_instances = [
                    instance
                    for instance in container_instances
                    if container_instance.arn != instance.arn
                ]

            else:
                valid_instances.append(container_instance)

        return valid_instances

    def validate(self) -> ValidatorResult:
        (
            versioned_attributes,
            non_versioned_attributes,
            list_attributes,
        ) = _split_attributes(self.service.requires_attributes)

        # validate versioned attributes first because they are more likely to be missing/incorrect
        if versioned_attributes:
            valid_instances_with_versioned_attributes = (
                self._validate_versioned_attributes(
                    versioned_attributes, self.cluster.container_instances
                )
            )

            # if there are versioned attributes required, but no instances have them, raise the exception
            if len(valid_instances_with_versioned_attributes) == 0:
                self._raise_exception()
            else:
                self.result.valid_instances.extend(
                    valid_instances_with_versioned_attributes
                )

        # then validate attributes on the instances that passed the versioned attributes validation
        if non_versioned_attributes:
            valid_instances_with_non_versioned_attributes = (
                self._validate_non_versioned_attributes(
                    non_versioned_attributes, self.cluster.container_instances
                )
            )

            # if there are non-versioned attributes required, but no instances have them, raise the exception
            if len(valid_instances_with_non_versioned_attributes) == 0:
                self._raise_exception()
            else:
                self.result.valid_instances.extend(
                    (
                        elem
                        for elem in valid_instances_with_non_versioned_attributes
                        if elem not in self.result.valid_instances
                    )
                )

        if list_attributes:
            valid_instances_with_list_attributes = self._validate_list_attributes(
                list_attributes, self.cluster.container_instances
            )

            if len(valid_instances_with_list_attributes) == 0:
                self._raise_exception()

            else:
                self.result.valid_instances.extend(
                    (
                        elem
                        for elem in valid_instances_with_list_attributes
                        if elem not in self.result.valid_instances
                    )
                )

        # no exceptions raised so return a successful result
        table = f"""
{'Instance ID':>15} | {'CPU remaining':>15} | {'CPU total':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-' * 90}
"""

        for ins in self.result.valid_instances:
            table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} | {ins.memory_remaining:>15}  | {ins.memory_total: >15} |\n"

        self.result.success = True
        self.result.message = (
            f"Service '{self.service.name}' can run on the '{self.cluster.name}' cluster. "
            f"At least one container instance has all the attributes required by the task definition."
        )
        self.result.verbose_message = (
            f"Service '{self.service.name}' can run on the '{self.cluster.name}' cluster. "
            f"Container instances that have all the attributes required by the task definition:\n{table}"
        )

        return self.result
