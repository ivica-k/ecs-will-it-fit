from willy.exceptions import NoPortsAvailableException
from willy.models import Service, Cluster, ValidatorResult


class NetworkValidator:
    def __init__(self, service: Service, cluster: Cluster):
        self.service: Service = service
        self.cluster: Cluster = cluster

    def validate(self) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        task_def_ports = self.service.all_ports
        a = 2
        for container_instance in self.cluster.container_instances:
            free_host_ports = [
                port
                for port in task_def_ports
                if port not in container_instance.all_ports
            ]

            # container instance has free ports (TCP and UDP) that the task def is requesting
            if free_host_ports == task_def_ports:
                result.valid_instances.append(container_instance)
            else:
                result.invalid_instances.append(container_instance)

        if len(result.valid_instances) == 0:
            result.success = False

            table = f"""
Container instances incapable of running the task definition:\n
{'Instance ID':>15} | {'Used ports (TCP)':>15} | {'Used ports (UDP)':>15} |
{'-' * 53}
"""

            for ins in result.invalid_instances:
                ports_tcp = ", ".join([str(elem) for elem in ins.ports_tcp])
                ports_udp = ", ".join([str(elem) for elem in ins.ports_udp])
                table += (
                    f"{ins.instance_id:>15} | {ports_tcp:>15} | {ports_udp: >15} |\n"
                )

            msg = (
                f"Service '{self.service.name}' can not run on the '{self.cluster.name}' "
                f"cluster. The service requires ports {self.service.all_ports} that are used on all "
                f"container instances in the cluster."
            )

            result.message = msg
            result.verbose_message = f"{msg}\n{table}"

            raise NoPortsAvailableException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )
        else:
            result.success = True

        return result
