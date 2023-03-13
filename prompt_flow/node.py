import typing
from abc import ABC, abstractmethod
from pydantic import BaseModel, Extra, Field
from inspect import signature, iscoroutinefunction
from dataclasses import make_dataclass, field


class NodeBase(BaseModel, ABC, extra=Extra.allow):
    name: str
    inputs: typing.Optional[typing.Callable]
    func: typing.Callable
    outputs: typing.Optional[typing.Callable]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"('name': {self.name}, 'inputs': {self.inputs}, 'outputs': {self.outputs})"
        )

    def __hash__(self):
        return self.func.__hash__()


class SyncNode(NodeBase):
    def __call__(self, *args: typing.Any, **kwds: typing.Any):
        return self.func(*args, **kwds)


class AsyncNode(NodeBase):
    async def __call__(self, *args: typing.Any, **kwds: typing.Any):
        return await self.func(*args, **kwds)


NODE_TYPES = AsyncNode | SyncNode


def parse__doc__(func: typing.Callable) -> list[tuple[str, str]]:
    returns = list()
    docs = func.__doc__.split("\n")
    in_returns = False
    return_row_number = -1
    for row_number, row in enumerate(docs):
        if row.strip("\n ").lower() == "returns":
            in_returns = True
            return_row_number = row_number
        elif in_returns and (row_number - return_row_number) % 2 == 0:
            parts = row.split(" : ")
            if len(parts) == 2:
                returns.append(
                    (
                        parts[0].strip(),
                        f"typing.Optional[{parts[1].strip()}]",
                        Field(default=None, init=False),
                    )
                )
    return returns


type_map = dict()
type_map["typing.Dict"] = "dict"
type_map["typing.List"] = "list"
type_map["typing.Set"] = "set"
type_map["typing.FrozenSet"] = "frozenset"
type_map["typing.DefaultDict"] = "defaultdict"
type_map["typing.OrderedDict"] = "OrderedDict"
type_map["typing.ChainMap"] = "ChainMap"
type_map["typing.Counter"] = "Counter"
type_map["typing.Deque"] = "deque"
type_map["typing.Tuple"] = "tuple"
type_map["typing.NamedTuple"] = "namedtuple"
type_map["NamedTuple"] = "namedtuple"


def parse_input(class_str: str) -> str:
    class_name = class_str
    if class_str.startswith("<class '"):
        class_name = class_str[8:-2]
    elif class_str.startswith("<function "):
        class_name = class_str.split(" ")[1]
    if class_name in type_map:
        return type_map[class_name]
    return class_name


class NodeDataClass(BaseModel):
    __node_name: str = None

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    def __iadd__(self, other):
        return [self, other]

    # def __add__(self, other):


def build_node(func: typing.Callable) -> NODE_TYPES:
    name = func.__name__
    sig = signature(func)
    inputs = [
        (
            k,
            f"typing.Optional[{parse_input(str(v.annotation))}]",
            Field(default=None, init=False),
        )
        for k, v in sig.parameters.items()
    ]
    input_dataclass = make_dataclass(
        f"{name}_inputs", inputs, bases=(NodeDataClass,), init=False
    )
    outputs = parse__doc__(func)
    output_dataclass = make_dataclass(
        f"{name}_outputs", outputs, bases=(NodeDataClass,), init=False
    )

    if iscoroutinefunction(func):
        return AsyncNode(
            func=func, name=name, inputs=input_dataclass, outputs=output_dataclass
        )
    else:
        return SyncNode(
            func=func, name=name, inputs=input_dataclass, outputs=output_dataclass
        )
