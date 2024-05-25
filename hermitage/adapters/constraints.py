import typing


class Exclude:
    def __init__(self, *names: str):
        self._names = names

    def __call__(self, name: str, value: typing.Any) -> bool:
        return name in self._names
