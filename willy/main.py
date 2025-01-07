from sys import exit

import boto3

from willy.exceptions import (
    NotEnoughCPUException,
    NotEnoughMemoryException,
    MissingECSAttributeException,
    NoPortsAvailableException,
)
from willy.models import ValidatorResult
from willy.services import ECSService
from willy.validators import (
    CPUValidator,
    MemoryValidator,
    AttributesValidator,
    NetworkValidator,
)


def will_it_fit(service_name: str, cluster_name: str, verbose: bool = False):
    # red validacija https://aws.amazon.com/blogs/compute/amazon-ecs-task-placement/
    # cpu - ovde desired count
    # memory - ovde desired count
    # network
    # location
    # instance-type
    # custom-attributes
    # placement constraints - distinctInstance i memberOf

    ecs_client = boto3.client("ecs")
    ecs_service = ECSService(
        ecs_client=ecs_client, cluster_name=cluster_name, service_name=service_name
    )

    validators = [CPUValidator, MemoryValidator, NetworkValidator, AttributesValidator]
    result: ValidatorResult = ValidatorResult()
    valid_instances = ecs_service.cluster.container_instances

    try:
        for validator in validators:
            valid_instances = [
                elem for elem in valid_instances if elem not in result.invalid_instances
            ]

            result = validator().validate(
                cluster=ecs_service.cluster,
                service=ecs_service.service,
                container_instances=valid_instances,
            )

        message = f"Service '{service_name}' can be scheduled on the '{cluster_name}' cluster."

        if verbose:
            table = f"""
{'Instance ID':>19} | {'CPU remaining':>15} | {'CPU total':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-'*19:>19} | {'-'*15:>15} | {'-'*15:>15} | {'-'*16:>16} | {'-'*15:>15} |
"""

            for instance in valid_instances:
                table += f"{instance.instance_id:>15} | {instance.cpu_remaining:>15} | {instance.cpu_total: >15} | {instance.memory_remaining:>15}  | {instance.memory_total: >15} |\n"

            message += f"\n\nContainer instances on which service '{service_name}' can be scheduled:\n{table}"

        print(message)

    except (
        NotEnoughCPUException,
        NotEnoughMemoryException,
        MissingECSAttributeException,
        NoPortsAvailableException,
    ) as exc:
        exit(f"{exc.verbose_message}")
