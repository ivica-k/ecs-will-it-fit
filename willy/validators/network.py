from typing import List

from willy.exceptions import NoPortsAvailableException
from willy.models import Service, Cluster, ValidatorResult, ContainerInstance
from willy.validators import BaseValidator


class NetworkValidator(BaseValidator):
    def validate(
        self,
        cluster: Cluster,
        service: Service,
        container_instances: List[ContainerInstance],
    ) -> ValidatorResult:
        result: ValidatorResult = ValidatorResult()

        task_def_ports = service.all_ports

        for container_instance in cluster.container_instances:
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
Container instances incapable of running the service:\n
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
                f"Service '{service.name}' can not run on the '{cluster.name}' "
                f"cluster. The service requires ports {service.all_ports} that are used on all "
                f"container instances in the cluster."
            )

            result.message = msg
            result.verbose_message = f"{msg}\n{table}"

            print(result.message)
            print(result.verbose_message)

            raise NoPortsAvailableException(
                message=result.message,
                verbose_message=result.verbose_message,
                valid_instances=result.valid_instances,
                invalid_instances=result.invalid_instances,
            )
        else:
            table = f"""
Container instances capable of running the service:\n
{'Instance ID':>15} | {'Used ports (TCP)':>15} | {'Used ports (UDP)':>15} |
{'-' * 53}
"""

            for ins in result.valid_instances:
                ports_tcp = ", ".join([str(elem) for elem in ins.ports_tcp])
                ports_udp = ", ".join([str(elem) for elem in ins.ports_udp])
                table += (
                    f"{ins.instance_id:>15} | {ports_tcp:>15} | {ports_udp: >15} |\n"
                )

            result.success = True
            result.message = (
                f"Cluster '{cluster.name}' has all required ports to run containers from the '{service.name}' service."
            )
            result.verbose_message = (
                f"Cluster '{cluster.name}' has all required ports to run containers from the '{service.name}' service.\n"
                f"The following container instances have the following ports {service.all_ports} available:"
                f"\n{table}"
            )

        return result
