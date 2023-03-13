import asyncio
import sys
import typing
import uvloop

from functools import wraps
from pydantic import BaseModel
from inspect import signature


acceptable_types = typing.Any


class Node(BaseModel):
    name: str
    inputs: typing.Optional[typing.Dict[str, acceptable_types]]
    outputs: typing.Optional[typing.Dict[str, acceptable_types]]
    func: typing.Callable

    def __hash__(self):
        return self.func.__hash__()
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Graph(BaseModel):
    nodes: typing.Set = set()
    inputs: typing.Optional[typing.Dict[str, acceptable_types]]
    outputs: typing.Optional[typing.Dict[str, acceptable_types]]
    manifest: typing.Dict = dict()
    
    def add_node(self, f: typing.Union[typing.Callable, Node]):
        if not isinstance(f, Node):
            f = f()
        self.nodes.add(f)

    def build_graph(self):
        pass


def node(outputs: typing.Dict[str, acceptable_types] = None):
    def node_wrapper(func) -> Node:
        @wraps(func)
        def wrapped_node(*args, **kwargs) -> typing.Callable:
            name = func.__name__
            sig = signature(func)
            inputs = [(k, v.annotation) for k,v in sig.parameters.items()]
            return Node(func=func, name=name, inputs=inputs, outputs=outputs)
        return wrapped_node
    return node_wrapper


@node()
async def test_null():
    return

@node(
        outputs = {
            'a': int    
        }
)
async def test_0(obj_to_print:int):
    return obj_to_print

@node(
        outputs = {
            'a': dict[str, int]
        }
)
async def test_1(obj_to_print: dict[str, int]):
    return obj_to_print

@node(
        outputs = {
            'a': typing.Dict[str, int]
        }
)
async def test_2(obj_to_print: typing.Dict[str, int]):
    return obj_to_print

g = Graph()
g.add_node(test_null)
g.add_node(test_0)
g.add_node(test_1)
g.add_node(test_2)
print(g.nodes)


def test_f(f: typing.Callable):
    print(f.__name__)
    test = f()
    print(test.name)
    print(test.inputs)
    print(test.outputs)

async def main():
    for f in [test_null, test_0, test_1, test_2]:
        test_f(f)


if sys.version_info >= (3, 11):
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())
else:
    uvloop.install()
    asyncio.run(main())
