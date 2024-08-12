import collections.abc
import dataclasses
import operator
import typing

import zodchy

AND = operator.and_
OR = operator.or_


@dataclasses.dataclass(frozen=True)
class InvoiceElement:
    pass


@dataclasses.dataclass(frozen=True)
class MetaElement(InvoiceElement):
    pass


@dataclasses.dataclass(frozen=True)
class DataElement(InvoiceElement):
    pass


class Item(DataElement):
    def __init__(self, content: str | collections.abc.Mapping):
        self._content = content

    def __call__(self) -> str | collections.abc.Mapping:
        return self._content

    def __eq__(self, other: collections.abc.Callable):  # type: ignore[override]
        if not isinstance(other, Item):
            return NotImplemented

        return self() == other()


@dataclasses.dataclass(frozen=True)
class Clause(DataElement):
    name: str
    operation: zodchy.codex.query.FilterBit | zodchy.codex.query.OrderBit

    def __and__(self, other: typing.Self | 'ClauseExpression'):
        _self = Clause(name=self.name, operation=self.operation)
        if isinstance(other, type(self)):
            return ClauseExpression(_self) & other
        else:
            return other & _self  # type: ignore[operator]

    def __or__(self, other: typing.Self | 'ClauseExpression'):
        _self = Clause(name=self.name, operation=self.operation)
        if isinstance(other, type(self)):
            return ClauseExpression(_self) | other
        else:
            return other | _self  # type: ignore[operator]

    def __eq__(self, other: object):
        if not isinstance(other, Clause):
            raise NotImplemented
        return self.name == other.name


@dataclasses.dataclass(frozen=True)
class Slice(DataElement):
    operation: zodchy.codex.query.SliceBit


class ClauseExpression(DataElement):
    def __init__(self, *elements: typing.Union[Clause, collections.abc.Callable]):
        self._stack = list(elements) if elements else []

    def __and__(self, other: typing.Self | Clause) -> typing.Self:
        return self._merge(other, AND)

    def __or__(self, other: typing.Self | Clause) -> typing.Self:
        return self._merge(other, OR)

    def __iter__(self):
        yield from self._stack

    def __getitem__(self, item: int):
        return self._stack[item]

    def _merge(self, other: typing.Self | Clause, operation: collections.abc.Callable):
        if isinstance(other, Clause):
            return ClauseExpression(*self, other, operation)
        elif isinstance(other, ClauseExpression):
            return ClauseExpression(*self, *other, operation)


class Bucket(InvoiceElement):
    def __init__(
        self,
        name: str,
        *elements: InvoiceElement
    ):
        self._name = name
        self._elements = list(elements)
        self._qua = ''
        self._label = ''
        self._address = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str | None:
        return self._address or self._qua or self._name

    @property
    def qualified_name(self) -> str:
        parts = [
            self._name,
            self._qua,
            self._label
        ]
        return ":".join(parts)

    @property
    def substitution_name(self) -> str:
        if self._label:
            return self._label
        if self._qua:
            return self._qua
        return self._name

    def get_qua(self) -> str | None:
        return self._qua or None

    def get_label(self) -> str | None:
        return self._label or None

    def __iter__(self) -> collections.abc.Iterable[InvoiceElement | ClauseExpression | typing.Self]:
        yield from self._elements

    def __add__(self, other: InvoiceElement):
        if isinstance(other, Item):
            if any(other == e for e in self._elements if isinstance(e, Item)):
                return self
        self._elements.append(other)
        return self

    def qua(self, value: str) -> typing.Self:
        self._qua = value
        return self

    def label(self, value: str) -> typing.Self:
        if self._name != value:
            self._label = value
        return self


@dataclasses.dataclass(frozen=True)
class Total(MetaElement):
    pass


@dataclasses.dataclass(frozen=True)
class Upsert(MetaElement):
    clause: Clause | ClauseExpression


class Invoice:
    def __init__(self, *elements: Bucket):
        self._elements = elements

    def __iter__(self):
        yield from self._elements


ViewData = collections.abc.Iterable[collections.abc.MutableMapping]


class ViewMeta(typing.TypedDict):
    total: int | None


class View:
    def __init__(self, data: ViewData, meta: ViewMeta | None = None):
        self._data = data
        self._meta = meta

    @property
    def data(self) -> ViewData:
        return self._data

    @property
    def meta(self) -> ViewMeta | None:
        return self._meta
