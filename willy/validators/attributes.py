from willy.models import (
    TaskDefinition,
    Cluster,
    ValidatorResult,
    ContainerInstance,
    Service,
    Attribute,
)
from willy.exceptions import MissingECSAttributeException
import re

from typing import List

VERSION_REGEX = r"(.*?)(\d\.\d{1,})"


def _split_attr_version(attribute_name: str):
    return re.search(VERSION_REGEX, attribute_name).groups()


def _contains_version(attribute_name: str):
    return bool(re.match(VERSION_REGEX, attribute_name))


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
        return False, []

    return (
        sorted(list(set(lesser_than_or_equal_to_required)))
        == sorted([Attribute(name=elem.name) for elem in task_def_attributes]),
        greater_than_or_equal_to_required,
    )


class AttributesValidator:
    def __init__(self, service: Service, cluster: Cluster):
        self.service: Service = service
        self.cluster: Cluster = cluster

    def _split_attributes(self, attributes: List[Attribute]):
        versioned_attributes = []
        non_versioned_attributes = []

        for attr in attributes:
            if _contains_version(attr.name):
                versioned_attributes.append(attr)
            else:
                non_versioned_attributes.append(attr)

        return versioned_attributes, non_versioned_attributes

    def _validate_versioned_attributes(
        self, versioned_attributes: List, container_instances: List[ContainerInstance]
    ) -> (List[ContainerInstance], List[str]):
        valid_instances = []
        missing_attributes = []

        for container_instance in container_instances:
            versioned_instance_attributes, _ = self._split_attributes(
                container_instance.attributes
            )
            all_attributes_present = sorted(
                versioned_attributes, key=lambda attr: attr.name
            ) == sorted(versioned_instance_attributes, key=lambda attr: attr.name)

            if all_attributes_present:
                valid_instances.append(container_instance)
            else:
                (
                    all_attribute_lower_than_or_equal_to,
                    missing_attributes,
                ) = _compare_versioned_attribute(
                    task_def_attributes=versioned_attributes,
                    container_instance_attributes=container_instance.attributes,
                )

                if all_attribute_lower_than_or_equal_to:
                    valid_instances.append(container_instance)
                else:
                    missing_attributes.extend(missing_attributes)

        return valid_instances, missing_attributes

    def validate(self) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()
        missing_attributes = []

        versioned_attributes, non_versioned_attributes = self._split_attributes(
            self.service.requires_attributes
        )

        # validate versioned attributes first because they are more likely to be missing
        if versioned_attributes:
            (
                valid_instances_with_versioned_attributes,
                missing_attrs,
            ) = self._validate_versioned_attributes(
                versioned_attributes, self.cluster.container_instances
            )

            if len(valid_instances_with_versioned_attributes) == 0:
                missing_attrs_str = f"""{f"{chr(10)}".join([elem.name for elem in list(set(missing_attrs))])}"""

                result.verbose_message = (
                    f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
                    f"There are no container instances that have the attributes required by the task definition.\nMissing "
                    f"attribute(s):\n\n{missing_attrs_str}"
                )

                result.message = (
                    f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
                    f"There are no container instances that have the attributes required by the task definition."
                )

                raise MissingECSAttributeException(
                    message=result.message,
                    verbose_message=result.verbose_message,
                    valid_instances=result.valid_instances,
                    invalid_instances=result.invalid_instances,
                )
            else:
                result.valid_instances = valid_instances_with_versioned_attributes

        # then validate attributes on the instances that passed the versioned attributes validation
        else:
            valid_instances_with_versioned_attributes = []

        for container_instance in self.cluster.container_instances:
            # there's a chance that the list of attributes on the task def and the container instance are equal,
            # in which case the instance is considered valid.
            if (
                self.service.task_definition.requires_attributes
                == container_instance.attributes
            ):
                result.valid_instances.append(container_instance)

            else:
                for attr in non_versioned_attributes:
                    if attr not in container_instance.attributes:
                        missing_attributes.append(attr)

            if len(missing_attributes) > 0:
                result.invalid_instances.append(
                    {
                        "arn": container_instance.arn,
                        "reason": f"Missing attributes: {', '.join([elem.name for elem in missing_attributes])}",
                    }
                )

                # remove the current instance from the list of all valid instances by matching the ARN
                # this happens when an instance has one valid versioned attribute and one invalid non-versioned attribute
                result.valid_instances = [
                    instance
                    for instance in valid_instances_with_versioned_attributes
                    if container_instance.arn != instance.arn
                ]

            else:
                result.valid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            missing_attrs_str = (
                f"""{f"{chr(10)}".join([elem.name for elem in missing_attributes])}"""
            )

            result.verbose_message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
                f"There are no container instances that have the attributes required by the task definition. "
                f"Attribute(s) missing or incorrect on the container instance:\n\n{missing_attrs_str}"
            )

            result.message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' cluster. "
                f"There are no container instances that have the attributes required by the task definition."
            )

            raise MissingECSAttributeException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )

        else:
            table = f"""
{'Instance ID':>15} | {'CPU remaining':>15} | {'CPU total':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-' * 90}
"""

            for ins in result.valid_instances:
                table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} | {ins.memory_remaining:>15}  | {ins.memory_total: >15} |\n"

            result.success = True
            result.message = (
                f"Service '{self.service.name}' can run on the '{self.cluster.name}' cluster. "
                f"At least one container instance has all the attributes required by the task definition."
            )
            result.verbose_message = (
                f"Service '{self.service.name}' can run on the '{self.cluster.name}' cluster. "
                f"Container instances that have all the attributes required by the task definition:\n{table}"
            )

        return result
