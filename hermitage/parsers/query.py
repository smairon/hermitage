import dataclasses
import collections.abc
import inspect
import typing

import zodchy
from ..definition import contracts


class QueryParser:
    def __init__(self, query: zodchy.codex.cqea.Query):
        self._query = query
        self._mappers = None
        self._substitutes = {}

    def map(self, *mappers: collections.abc.Callable):
        self._mappers = mappers
        return self

    def sub(self, source_field: str, target_field: str):
        self._substitutes[source_field] = target_field
        return self

    def __iter__(self):
        if not self._query:
            return ()
        for field in dataclasses.fields(self._query):
            field_name = self._substitutes.get(field.name, field.name)
            value = getattr(self._query, field.name)
            if value is None:
                continue
            if _search_contract(
                _evoke_types_chain(field.type),
                zodchy.codex.query.ClauseBit
            ):
                if not isinstance(value, collections.abc.Sequence):
                    value = (value,)
                for v in value:
                    clause = contracts.Clause(field_name, v)
                    yield self._apply_mappers(clause)
            else:
                yield contracts.Clause(
                    field_name,
                    zodchy.codex.query.EQ(getattr(self._query, field_name))
                )

    def _apply_mappers(self, clause: contracts.Clause):
        if self._mappers:
            for mapper in self._mappers:
                clause = mapper(clause)
        return clause


def _evoke_types_chain(annotation):
    _origin = typing.get_origin(annotation)
    if not _origin:
        return zodchy.types.Empty if annotation is inspect.Parameter.empty else annotation
    else:
        args = typing.get_args(annotation)
        chain = [_origin]
        if len(args) == 1:
            r = _evoke_types_chain(args[0])
            if isinstance(r, collections.abc.Sequence):
                chain.extend(r)
            else:
                chain.append(r)
        else:
            chain.append(tuple(_evoke_types_chain(arg) for arg in args))
    return chain


def _search_contract(
    haystack: collections.abc.Sequence | type,
    *needles: type
) -> type | None:
    haystack = haystack if isinstance(haystack, collections.abc.Sequence) else (haystack,)
    if collections.abc.Callable in haystack:
        return
    for element in haystack:
        if isinstance(element, collections.abc.Sequence):
            if result := _search_contract(element, *needles):
                return result
        else:
            if any(
                needle is element or
                (hasattr(element, '__mro__') and needle in element.__mro__)
                for needle in needles
            ):
                return element
