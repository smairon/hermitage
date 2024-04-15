import abc
import collections.abc
import dataclasses
import functools
import typing
import uuid
import enum
import itertools
from collections import deque

from zodchy import codex


class Address:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def __hash__(self):
        return uuid.uuid5(uuid.NAMESPACE_DNS, self.value).int

    def __eq__(self, other: typing.Self):
        return self.value == other.value


class Namespace:
    def __init__(
        self,
        value: str | collections.abc.Sequence[str]
    ):
        if isinstance(value, str):
            self._data = value.strip().split('.') if value else []
        elif isinstance(value, collections.abc.Sequence):
            self._data = value
        else:
            raise TypeError("Undefined namespace value")

    def __add__(self, other: typing.Self) -> typing.Self:
        if not self:
            return other
        if not other:
            return self
        return type(self)(
            list(_remove_duplicates(itertools.chain(self._data, other)))
        )

    def __iter__(self) -> collections.abc.Generator[typing.Self, None, None]:
        for element in self._data:
            yield type(self)(element)

    def __getitem__(self, index: int) -> typing.Self | None:
        if index < len(self._data):
            return type(self)(self._data[index])

    def __bool__(self) -> bool:
        return bool(self._data)

    def first(self) -> typing.Self | None:
        return type(self)(self._data[0])

    def last(self) -> typing.Self | None:
        return type(self)(self._data[len(self._data) - 1])

    def part(
        self,
        end_index: int,
        start_index: int = 0
    ) -> typing.Self:
        return type(self)(".".join(self._data[start_index:end_index]))

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return ".".join(self._data)

    def __eq__(self, other: typing.Self) -> bool:
        return str(self) == str(other)

    def __hash__(self):
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(self)).int


class InvoiceElement(abc.ABC):
    def __init__(self):
        self._namespace = None
        self._fixed_namespace = None

    def set_namespace(
        self,
        namespace: Namespace
    ):
        if self._fixed_namespace:
            self._namespace = (namespace.part(-1) if len(namespace) > 1 else namespace) + self._fixed_namespace
        else:
            self._namespace = namespace
        return self

    @property
    def namespace(self) -> Namespace:
        return self._namespace

    @property
    def address(self) -> Address | None:
        return


class DataElement(InvoiceElement):
    pass


class MetaElement(InvoiceElement):
    pass


class Item(DataElement):
    def __init__(
        self,
        name: str,
        *elements: typing.Any
    ):
        super().__init__()
        self._name = name
        self._invoice = None
        self._address = None
        self._fixed_namespace = None
        self._distribute(elements)

    def set_namespace(
        self,
        namespace: Namespace
    ):
        super().set_namespace(namespace)
        if self._invoice:
            self._invoice.set_namespace(self._namespace.first() + self._invoice.namespace)

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> Address | None:
        return self._address

    @property
    def invoice(self) -> typing.Any:
        return self._invoice

    def __eq__(self, other: typing.Self):
        return self._name == other.name

    def __hash__(self):
        return uuid.uuid5(uuid.NAMESPACE_DNS, self.name).int

    def _distribute(self, elements: collections.abc.Iterable):
        for element in elements:
            if isinstance(element, str):
                self._address = Address(element)
            elif isinstance(element, Invoice):
                self._invoice = element
            elif isinstance(element, Address):
                self._address = element
            elif isinstance(element, Namespace):
                self._fixed_namespace = element


class Row(DataElement):
    def __init__(self, **data):
        super().__init__()
        self._data = data

    def update(self, key: str, value: typing.Any):
        if key in self._data:
            self._data[key] = value
        return self

    def delete(self, *keys: str):
        for key in keys:
            if key in self._data:
                del self._data[key]
        return self

    def insert(self, key: str, value: typing.Any):
        if key not in self._data:
            self._data[key] = value
        return self

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, item: str):
        return self._data.get(item)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for key in self._data:
            yield key

    def as_dict(self):
        return self._data


class LogicalOperator(enum.Enum):
    AND = enum.auto()
    OR = enum.auto()


class Clause(InvoiceElement):
    def __init__(
        self,
        *operands: typing.Any
    ):
        super().__init__()
        self._stack = None
        self._address = None
        self._operation = None
        self._kind = None
        self._distribute(deque(operands))

    @property
    def kind(self) -> type[codex.query.ClauseBit]:
        return self._kind

    @property
    def address(self) -> Address | None:
        return self._address

    @property
    def operation(self) -> typing.Self | codex.query.ClauseBit:
        return self._operation

    def __and__(self, other: typing.Self):
        return type(self)(
            LogicalOperator.AND,
            self,
            other
        )

    def __or__(self, other: typing.Self):
        return type(self)(
            LogicalOperator.OR,
            self,
            other
        )

    def __iter__(self):
        if self._stack is None:
            yield self
        else:
            for operand in self._stack:
                if hasattr(operand, 'kind') and operand.kind is LogicalOperator:
                    yield from operand
                else:
                    yield operand

    def _distribute(self, operands: deque):
        while len(operands) > 0:
            operand = operands.pop()
            if isinstance(operand, str):
                if len(parts := operand.split('.')) > 1:
                    operands.append(Address(parts[-1]))
                    operands.append(Namespace(".".join(parts[:-1])))
                else:
                    operands.append(Address(operand))
                continue
            if isinstance(operand, Address):
                self._address = operand
            if isinstance(operand, Namespace):
                self._fixed_namespace = operand
            if isinstance(operand, codex.query.ClauseBit) or isinstance(operand, LogicalOperator):
                self._operation = operand
            if isinstance(operand, Clause) or isinstance(operand, LogicalOperator):
                self._add_to_stack(operand)
        self._kind = type(self.operation)

    def _add_to_stack(self, operand: typing.Any):
        if self._stack is None:
            self._stack = deque()
        self._stack.append(operand)


class Invoice:
    def __init__(
        self,
        namespace: Namespace | str,
        *elements: InvoiceElement | str
    ):
        self._namespace = _normalize_namespace(namespace)
        self._elements = list(elements)
        self._distribute_elements()

    @property
    def elements(self) -> collections.abc.Iterable[InvoiceElement]:
        return self._elements

    @property
    def namespace(self) -> Namespace:
        return self._namespace

    @property
    def items(self) -> list[Item]:
        return self._items

    @property
    def meta(self) -> list[MetaElement]:
        return self._meta

    @property
    def clauses(self) -> list[Clause]:
        return self._clauses

    @functools.cached_property
    def rows(self) -> list[Row]:
        return self._rows

    def set_namespace(
        self,
        namespace: Namespace
    ):
        if isinstance(namespace, Namespace):
            self._namespace = namespace
            self._distribute_elements()
        return self

    def __iter__(self) -> typing.Generator[InvoiceElement, None, None]:
        for element in itertools.chain(self._items, self._clauses, self._rows, self._meta):
            yield element

    def __add__(self, other: InvoiceElement):
        if isinstance(other, Item) and any(filter(lambda x: x.address == other.address, self._items)):
            return self
        self._elements.append(other)
        self._distribute_element(other)
        return self

    def _distribute_elements(self):
        self._items = list()
        self._meta = list()
        self._clauses = list()
        self._rows = list()
        for element in self._elements:
            self._distribute_element(element)

    def _distribute_element(
        self,
        element: InvoiceElement
    ):
        element = _normalize_element(element)
        if isinstance(element, Item):
            element.set_namespace(self._namespace)
            self._items.append(element)
        elif isinstance(element, MetaElement):
            element.set_namespace(self._namespace)
            self._meta.append(element)
        elif isinstance(element, Clause):
            element.set_namespace(self._namespace)
            self._clauses.append(element)
        elif isinstance(element, Row):
            self._rows.append(element)


@dataclasses.dataclass
class View:
    data: collections.abc.Iterable[collections.abc.MutableMapping]
    meta: collections.abc.MutableMapping


class Plugin(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_beacon(cls) -> type[MetaElement]:
        raise NotImplementedError


class ReadPlugin(Plugin, abc.ABC):
    def __init__(self, data: collections.abc.Sequence[collections.abc.Mapping]):
        self._data = data

    @classmethod
    def get_query_builder_plugin(cls) -> collections.abc.Callable: ...

    def get_mappers(self) -> collections.abc.Iterable[collections.abc.Callable]: ...

    def get_result(self) -> dict[str, typing.Any]: ...


class WritePlugin(Plugin, abc.ABC):
    async def __call__(self, invoice: Invoice) -> Invoice:
        pass


class PluginRegistry:
    def __init__(self, *plugins: type[Plugin]):
        self._plugins = {
            plugin.get_beacon(): plugin
            for plugin in plugins
        }

    def get(self, key: type[MetaElement]):
        return self._plugins.get(key)

    def items(self):
        return self._plugins.items()

    def keys(self):
        return self._plugins.keys()

    def values(self):
        return self._plugins.values()

    def __iter__(self):
        for key in self._plugins:
            yield key

    def __getitem__(self, key: type[MetaElement]):
        return self._plugins[key]


def _remove_duplicates(elements: collections.abc.Iterable[str]) -> collections.abc.Generator[str]:
    previous = None
    for element in map(str, elements):
        if element != previous:
            yield element
            previous = element


def _normalize_namespace(value: typing.Any) -> typing.Any:
    if isinstance(value, str):
        return Namespace(value)
    return value


def _normalize_address(value: typing.Any) -> typing.Any:
    if isinstance(value, str):
        return Address(value)
    return value


def _normalize_element(value: typing.Any) -> typing.Any:
    if isinstance(value, str):
        address = _normalize_address(value)
        return Item(value, address)
    return value
