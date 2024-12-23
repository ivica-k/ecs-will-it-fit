from typing import List

from willy.models import ContainerInstance


class BaseException(Exception):
    def __init__(
        self,
        message: str,
        verbose_message: str = "",
        valid_instances: List[ContainerInstance] = None,
        invalid_instances: List[ContainerInstance] = None,
    ):
        super().__init__(message)
        self.message = message
        self.verbose_message = verbose_message
        self.valid_instances = [] if valid_instances is None else valid_instances
        self.invalid_instances = [] if invalid_instances is None else invalid_instances


class NotEnoughCPUException(BaseException):
    def __init__(
        self,
        message: str,
        verbose_message: str = "",
        valid_instances: List[ContainerInstance] = None,
        invalid_instances: List[ContainerInstance] = None,
    ):
        super().__init__(message, verbose_message, valid_instances, invalid_instances)


class NotEnoughMemoryException(BaseException):
    def __init__(
        self,
        message: str,
        verbose_message: str = "",
        valid_instances: List[ContainerInstance] = None,
        invalid_instances: List[ContainerInstance] = None,
    ):
        super().__init__(message, verbose_message, valid_instances, invalid_instances)


class MissingECSAttributeException(BaseException):
    def __init__(
        self,
        message: str,
        verbose_message: str = "",
        valid_instances: List[ContainerInstance] = None,
        invalid_instances: List[ContainerInstance] = None,
    ):
        super().__init__(message, verbose_message, valid_instances, invalid_instances)


class NoPortsAvailableException(BaseException):
    def __init__(
        self,
        message: str,
        verbose_message: str = "",
        valid_instances: List[ContainerInstance] = None,
        invalid_instances: List[ContainerInstance] = None,
    ):
        super().__init__(message, verbose_message, valid_instances, invalid_instances)
