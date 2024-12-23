from willy.models import Service, Cluster, ValidatorResult
from willy.exceptions import NotEnoughMemoryException


class MemoryValidator:
    def __init__(self, service: Service, cluster: Cluster):
        self.service: Service = service
        self.cluster = cluster

    def validate(self) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        for container_instance in self.cluster.container_instances:
            if container_instance.memory_remaining > self.service.total_memory_needed:
                result.valid_instances.append(container_instance)
            else:
                result.invalid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            table = f"""
Container instances incapable of running the task definition:\n
{'Instance ID':>15} | {'Memory remaining':>15} | {'Memory total':>15} |
{'-' * 53}
"""

            for ins in result.invalid_instances:
                table += f"{ins.instance_id:>15} | {ins.memory_remaining:>15} | {ins.memory_total: >15} |\n"

            result.verbose_message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' "
                f"cluster. There are no container instances that meet the hardware requirements of "
                f"{self.service.total_memory_needed} memory units.\n{table}"
            )
            result.message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' "
                f"cluster. Number of required memory units is {self.service.total_memory_needed} but the "
                f"cluster has {self.cluster.memory_remaining} memory units available across "
                f"{len(self.cluster.container_instances)} container instance(s)."
            )

            raise NotEnoughMemoryException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )

        else:
            result.success = True
            result.message = (
                f"Service '{self.service.name}' can run on the '{self.cluster.name}' "
                f"cluster."
            )

            result.verbose_message = "memory valja"

        return result
