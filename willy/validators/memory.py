from typing import List
from xml.sax.handler import property_interning_dict

from willy.exceptions import NotEnoughMemoryException
from willy.models import Service, Cluster, ValidatorResult, ContainerInstance
from willy.validators import BaseValidator


class MemoryValidator(BaseValidator):
    def validate(
        self,
        cluster: Cluster,
        service: Service,
        container_instances: List[ContainerInstance],
    ) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        for container_instance in container_instances:
            if container_instance.memory_remaining > service.total_memory_needed:
                result.valid_instances.append(container_instance)
            else:
                result.invalid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            table = f"""
Container instances incapable of running the service:\n
{'Instance ID':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-' * 53}
"""

            for ins in result.invalid_instances:
                table += f"{ins.instance_id:>15} | {ins.memory_remaining:>15} | {ins.memory_total: >15} |\n"

            result.verbose_message = (
                f"Service '{service.name}' can not run on the '{cluster.name}' "
                f"cluster. There are no container instances that meet the hardware requirements of "
                f"{service.total_memory_needed} memory units.\n{table}"
            )
            result.message = (
                f"Service '{service.name}' can not run on the '{cluster.name}' "
                f"cluster. Number of required memory units is {service.total_memory_needed} but the "
                f"cluster has {cluster.memory_remaining} memory units available across "
                f"{len(cluster.container_instances)} container instance(s)."
            )

            raise NotEnoughMemoryException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )

        else:
            table = f"""
Container instances capable of running the service:\n
{'Instance ID':>18} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-' * 53}
"""
            for ins in result.valid_instances:
                table += f"{ins.instance_id:>15} | {ins.memory_remaining:>15} | {ins.memory_total: >15} |\n"
            result.success = True
            result.message = (
                f"Cluster '{cluster.name}' has enough memory to run containers from the '{service.name}' service."
            )

            result.verbose_message = (
                f"Cluster '{cluster.name}' has enough memory to run containers from the '{service.name}' service.\n"
                f"The following container instances meet the hardware requirements of "
                f"{service.total_memory_needed} memory.\n{table}"
            )

        return result
