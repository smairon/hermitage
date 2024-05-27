import typing

import zodchy
from ..notation.default import Clause
from ..definitions.contracts.adapters import TransformerContract


class Replace(TransformerContract):
    def __init__(
        self,
        search_field: str,
        replace_field: str | None = None,
        replace_entity: typing.Any = None,
    ):
        super().__init__(search_field)
        self._replace_field = replace_field or search_field
        self._replace_entity = replace_entity

    def _apply_value(self, value: typing.Any):
        if callable(self._replace_entity):
            return self._replace_entity(value)
        return value

    def __call__(self, clause: Clause):
        operation = clause.operation
        if self._replace_entity is not None:
            if isinstance(operation, zodchy.codex.query.SET):
                operation = zodchy.codex.query.SET(
                    *[self._apply_value(v) for v in operation.value]
                )
            else:
                operation = type(operation)(self._apply_value(operation.value))
        clause = Clause(
            self._replace_field,
            operation
        )
        return clause
