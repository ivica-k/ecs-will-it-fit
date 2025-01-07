from abc import abstractmethod
from typing import List

from willy.models import Cluster, Service, ContainerInstance, ValidatorResult


class BaseValidator(object):
    @abstractmethod
    def validate(
        self,
        cluster: Cluster,
        service: Service,
        container_instances: List[ContainerInstance],
    ) -> ValidatorResult:
        raise NotImplementedError()
