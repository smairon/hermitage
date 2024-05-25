import abc
import typing


class ModifierContract(abc.ABC):
    def __init__(self, field_name: str):
        self.field_name = field_name

    @abc.abstractmethod
    def __call__(self, value: typing.Any): ...


class ConstraintContract(ModifierContract, abc.ABC):
    @abc.abstractmethod
    def __call__(self, value: typing.Any) -> bool: ...


class TransformerContract(ModifierContract, abc.ABC):
    @abc.abstractmethod
    def __call__(self, value: typing.Any) -> typing.Any: ...
