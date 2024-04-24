import typing
import enum

import zodchy
from ..definition import contracts

T = typing.TypeVar('T')


class ReferenceContract(typing.Sized, typing.Protocol):
    def __call__(self, value: enum.Enum) -> T: ...

    def __getitem__(self, key: T) -> enum.Enum: ...

    def get(self, key: T): ...


class ClauseInjector:
    def __init__(
        self,
        reference: ReferenceContract,
        search_key: str,
        injection_key: str | None = None
    ):
        super().__init__()
        self._search_key = search_key
        self._injection_key = injection_key
        self._reference = reference

    def __call__(self, clause: contracts.Clause):
        if str(clause.address) == self._search_key:
            operation = clause.operation
            if isinstance(operation, zodchy.codex.query.SET):
                operation = zodchy.codex.query.SET(
                    *[self._reference(v) for v in operation.value]
                )
            else:
                operation = type(operation)(self._reference(operation.value))
            clause = contracts.Clause(
                contracts.Address(self._injection_key),
                operation
            ).set_namespace(clause.namespace)
        return clause
