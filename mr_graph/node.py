import typing
from abc import ABC
from pydantic import Field
from inspect import signature, iscoroutinefunction
from dataclasses import make_dataclass
from mr_graph.node_data_class import (
    NodeDataClass,
    parse_annotation,
    parse_default,
    parse_doc,
)


class NodeBase(ABC):
    """The NodeBase is the abstract class which is inherited to define the nodes of the execution graph.

    Attributes:
        name (str): Name for the node. Usually derived from the function it wraps.
        inputs (typing.Callable, optional): a function to create a dataclass which will be used as input for the function.
        func (typing.Callable): The function to be called for this node in the graph.
        outputs (typing.Callable, optional): a function to create a dataclass which will be used to create an output for the function.

    Args:
        ABC: Abstract base class.
    """

    name: str
    inputs: typing.Optional[typing.Callable]
    func: typing.Callable
    outputs: typing.Optional[typing.Callable]

    def __init__(self, name, inputs, func, outputs):
        self.name = name
        self.inputs = inputs
        self.func = func
        self.outputs = outputs

    def __repr__(self) -> str:
        return (
            f"('name': {self.name}, 'inputs': {self.inputs}, 'outputs': {self.outputs})"
        )

    def __hash__(self) -> int:
        return self.func.__hash__()


class SyncNode(NodeBase):
    """For blocking functions.

    Args:
        NodeBase: Inherited class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> NodeDataClass:
        return self.func(*args, **kwds)


class AsyncNode(NodeBase):
    """For non-blocking (async) functions.

    Args:
        NodeBase: Inherited class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(
        self, *args: typing.Any, **kwds: typing.Any
    ) -> typing.Awaitable[NodeDataClass]:
        return await self.func(*args, **kwds)


NODE_TYPES = typing.Union[AsyncNode, SyncNode]
"""Typing.Union for all valid node types
"""


def build_node(func: typing.Callable) -> NODE_TYPES:
    """Generate a node. Can be ASync or blocking depending on the method.

    Args:
        func (typing.Callable): The function used in the node.

    Returns:
        NODE_TYPES: Any valid node type. Determined by the function that's being wrapped.
    """
    name = func.__name__
    sig = signature(func)
    inputs = [
        (
            k,
            f"typing.Optional[{parse_annotation(str(v.annotation))}]",
            Field(default=parse_default(str(v))),
        )
        for k, v in sig.parameters.items()
    ]
    input_dataclass = make_dataclass(
        f"{name}_inputs", inputs, bases=(NodeDataClass,), init=False
    )
    outputs = parse_doc(func)
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
