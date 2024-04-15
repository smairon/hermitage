import zodchy
import zodchy_patterns
from ..definition import contracts


class ClauseInjector:
    def __init__(
        self,
        reference: zodchy_patterns.Reference,
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
