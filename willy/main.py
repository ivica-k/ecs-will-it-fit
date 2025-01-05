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


# def will_it_fit(service: Service, cluster: Cluster):
def will_it_fit(service: str, cluster: str, verbose: bool = False):
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
        ecs_client=ecs_client, cluster_name=cluster, service_name=service
    )

    validators = [CPUValidator, MemoryValidator, NetworkValidator, AttributesValidator]
    rez: ValidatorResult = ValidatorResult()

    try:
        for validator in validators:
            ecs_service.cluster.container_instances = [
                elem
                for elem in ecs_service.cluster.container_instances
                if elem not in rez.invalid_instances
            ]
            rez = validator(ecs_service.service, ecs_service.cluster).validate()

        message = f"Service '{service}' can be scheduled on the '{cluster}' cluster."

        if verbose:
            table = f"""
{'Instance ID':>19} | {'CPU remaining':>15} | {'CPU total':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-'*19:>19} | {'-'*15:>15} | {'-'*15:>15} | {'-'*16:>16} | {'-'*15:>15} |
"""

            for ins in rez.valid_instances:
                table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} | {ins.memory_remaining:>15}  | {ins.memory_total: >15} |\n"

            message += f"\n\nContainer instances on which service '{service}' can be scheduled:\n{table}"

        print(message)

    except (
        NotEnoughCPUException,
        NotEnoughMemoryException,
        MissingECSAttributeException,
        NoPortsAvailableException,
    ) as exc:
        exit(f"{exc.verbose_message}")
