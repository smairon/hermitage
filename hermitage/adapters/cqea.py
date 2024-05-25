import typing
import collections.abc
import dataclasses
import inspect

import zodchy

from ..notation.default import (
    InvoiceElement,
    Item,
    Slice,
    Clause
)
from ..definitions.contracts.adapters import (
    ModifierContract,
    ConstraintContract,
    TransformerContract
)


class Adapter:
    def __call__(
        self,
        message: zodchy.codex.cqea.Query | zodchy.codex.cqea.WriteEvent,
        *modifiers: ModifierContract
    ) -> collections.abc.Generator[InvoiceElement, None, None]:
        indexed = collections.defaultdict(list)
        for modifier in modifiers:
            indexed[modifier.field_name].append(modifier)
        if isinstance(message, zodchy.codex.cqea.Query):
            return self._parse_query(message, indexed)
        elif isinstance(message, zodchy.codex.cqea.WriteEvent):
            return self._parse_write_event(message, indexed)

    def _parse_query(
        self,
        query: zodchy.codex.cqea.Query,
        modifiers: collections.abc.Mapping[str, list[ModifierContract]]
    ):
        for field in dataclasses.fields(query):
            value = getattr(query, field.name)
            if self._is_declined(field.name, value, modifiers):
                continue
            if value is zodchy.types.Empty:
                continue
            if _search_contract(
                _evoke_types_chain(field.type),
                zodchy.codex.query.ClauseBit
            ):
                if not isinstance(value, collections.abc.Sequence):
                    value = (value,)
                for v in value:
                    if isinstance(v, zodchy.codex.query.SliceBit):
                        result = Slice(v)
                    else:
                        result = Clause(field.name, v)
                    yield self._apply_transformers(
                        field.name,
                        result,
                        modifiers
                    )
            else:
                yield self._apply_transformers(
                    field.name,
                    Clause(
                        field.name,
                        zodchy.codex.query.EQ(getattr(query, field.name)),
                    ),
                    modifiers
                )

    @staticmethod
    def _is_declined(
        field_name: str,
        field_value: typing.Any,
        modifiers: collections.abc.Mapping[str, list[ModifierContract]]
    ):
        return any(
            constraint(field_value)
            for constraint in filter(lambda x: isinstance(x, ConstraintContract), modifiers.get(field_name, ()))
        )

    @staticmethod
    def _apply_transformers(
        field_name: str,
        clause: Clause,
        modifiers: collections.abc.Mapping[str, list[ModifierContract]]
    ):
        for transformer in filter(
            lambda x: isinstance(x, TransformerContract),
            modifiers.get(field_name, ())
        ):
            clause = transformer(clause)
        return clause

    def _parse_write_event(
        self,
        event: zodchy.codex.cqea.WriteEvent,
        modifiers: collections.abc.Mapping[str, list[ModifierContract]]
    ):
        data = {}
        for field in dataclasses.fields(event):
            value = getattr(event, field.name)
            if self._is_declined(field.name, value, modifiers):
                continue
            data[field.name] = self._apply_transformers(field.name, value, modifiers)
        yield Item(data)


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
