from typing import List

from willy.exceptions import NotEnoughCPUException
from willy.models import Cluster, ValidatorResult, Service, ContainerInstance
from willy.validators import BaseValidator


class CPUValidator(BaseValidator):
    def validate(
        self,
        cluster: Cluster,
        service: Service,
        container_instances: List[ContainerInstance],
    ) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        for container_instance in container_instances:
            if container_instance.cpu_remaining >= service.total_cpu_needed:
                result.valid_instances.append(container_instance)
            else:
                result.invalid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            table = f"""
Container instances incapable of running the service:\n
{'Instance ID':>15} | {'CPU remaining':>15} | {'CPU total':>15} |
{'-'*53}
"""

            for ins in result.invalid_instances:
                table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} |\n"

            result.verbose_message = (
                f"Service '{service.name}' can not run on the '{cluster.name}' "
                f"cluster. There are no container instances that meet the hardware requirements of "
                f"{service.total_cpu_needed} CPU units.\n{table}"
            )
            result.message = (
                f"Service '{service.name}' can not run on the '{cluster.name}' "
                f"cluster. Number of required CPU units is {service.total_cpu_needed} but the cluster has "
                f"{cluster.cpu_remaining} CPU units available across {len(cluster.container_instances)} "
                f"container instances."
            )

            raise NotEnoughCPUException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )

        else:
            table = f"""
Container instances capable of running the service:\n
{'Instance ID':>18} | {'CPU remaining':>15} | {'CPU total':>15} |
{'-' * 53}
"""

            for ins in result.valid_instances:
                table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} |\n"
            result.success = True
            result.message = (
                f"Cluster '{cluster.name}' has enough CPU units to run containers from the '{service.name}' service."
            )
            result.verbose_message = (
                f"Cluster '{cluster.name}' has enough CPU units to run containers from the '{service.name}' service.\n"
                f"The following container instances meet the hardware requirements of "
                f"{service.total_cpu_needed} CPU units.\n{table}"
            )

        return result
