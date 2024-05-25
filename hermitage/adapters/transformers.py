import typing

import zodchy
from ..notation.default import Clause
from ..definitions.contracts.adapters import TransformerContract


class Inject(TransformerContract):
    def __init__(
        self,
        field_name: str,
        injection_entity: typing.Any,
        injection_field: str | None = None
    ):
        super().__init__(field_name)
        self._injection_field = injection_field or field_name
        self._injection_entity = injection_entity

    def _apply_value(self, value: typing.Any):
        if callable(self._injection_entity):
            return self._injection_entity(value)
        return value

    def __call__(self, clause: Clause):
        operation = clause.operation
        if isinstance(operation, zodchy.codex.query.SET):
            operation = zodchy.codex.query.SET(
                *[self._apply_value(v) for v in operation.value]
            )
        else:
            operation = type(operation)(self._apply_value(operation.value))
        clause = Clause(
            self._injection_field,
            operation
        )
        return clause
