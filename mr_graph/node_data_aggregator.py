from uuid import uuid4 as uuid
from mr_graph.node_data_class import NodeDataClass
from mr_graph.node import SyncNode
import typing
from dataclasses import make_dataclass
from pydantic import Field


class NodeDataAggregator:
    inputs: dict[str, tuple[str, str]]  # keys to pull input
    node: typing.Callable
    output: typing.Callable

    def __init__(self, name: str):
        self.result_name = name
        self.name = f"{name}_{str(uuid())}"
        setattr(self, "__node_name", self.name)
        self.inputs = dict()
        null_function = lambda x: None
        outputs = [
            (
                self.result_name,
                f"typing.Optional[list[typing.Any]]",
                Field(default=None, init=False),
            )
        ]
        self.outputs = make_dataclass(f"{self.name}_outputs", outputs, bases=(NodeDataClass,), init=False)
        self.output = self.outputs()
        self.node = SyncNode(
            name=self.name,
            inputs=null_function,
            func=self.__call__,
            outputs=self.output,
        )
    
    def __iadd__(self, other) -> "NodeDataAggregator":
        """adding to NodeDataAggregator.

        Args:
            other (NodeDataTracker): other to add

        Raises:

        Returns:
            NodeDataAggregator: All attrs are added to self and returned as the result of +.
        """
        if isinstance(other, tuple) and other[0] == "mr_graph_node":
            (_, key, value) = other
            i_name = f"{self.result_name}_{len(self.inputs)}"
            self.inputs[i_name] = (key, value)
            return self
        elif isinstance(other, NodeDataAggregator):
            for key, value in other.inputs.items():
                i_name = f"{self.result_name}_{len(self.inputs)}"
                self.inputs[i_name] = value
            return self
        else:
            raise Exception("Adding a not NodeDataClass to a NodeDataClass")

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> NodeDataClass:
        return list(kwds.values())

    def __repr__(self) -> str:
        return (
            f"({self.node_name}, 'inputs': {self.inputs}, 'outputs': {self.outputs})"
        )

    def __hash__(self) -> int:
        return self.func.__hash__()
