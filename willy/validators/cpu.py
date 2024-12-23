from willy.models import TaskDefinition, Cluster, ValidatorResult, Service
from willy.exceptions import NotEnoughCPUException


class CPUValidator:
    def __init__(self, service: Service, cluster: Cluster):
        self.service: Service = service
        self.cluster: Cluster = cluster

    def validate(self) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        for container_instance in self.cluster.container_instances:
            if container_instance.cpu_remaining >= self.service.total_cpu_needed:
                result.valid_instances.append(container_instance)
            else:
                result.invalid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            table = f"""
Container instances incapable of running the task definition:\n
{'Instance ID':>15} | {'CPU remaining':>15} | {'CPU total':>15} |
{'-'*53}
"""

            for ins in result.invalid_instances:
                table += f"{ins.instance_id:>15} | {ins.cpu_remaining:>15} | {ins.cpu_total: >15} |\n"

            result.verbose_message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' "
                f"cluster. There are no container instances that meet the hardware requirements of "
                f"{self.service.total_cpu_needed} CPU units.\n{table}"
            )
            result.message = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' "
                f"cluster. Number of required CPU units is {self.service.total_cpu_needed} but the cluster has "
                f"{self.cluster.cpu_remaining} CPU units available across {len(self.cluster.container_instances)} "
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
                f"Cluster '{self.cluster.name}' has enough CPU units to run containers from the '{self.service.name}'"
                f"service."
            )
            result.verbose_message = f"{table}"

            # TODO: missing a verbose message

        return result
