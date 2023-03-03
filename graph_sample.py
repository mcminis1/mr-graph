import asyncio
import sys
import uvloop
from functools import wraps
from pydantic import BaseModel
from typing import Dict, Callable, List, Set, Optional, Tuple, Type
from inspect import signature


class Node(BaseModel):
    name: str
    inputs: Optional[List[Tuple[str,Type]]]
    outputs: Optional[List[Tuple[str,Type]]]
    func: Callable


class Graph(BaseModel):
    nodes: Set
    inputs: Optional[List[Tuple[str,Type]]]
    outputs: Optional[List[Tuple[str,Type]]]
    manifest: Dict


def node(func) -> Node:
    @wraps(func)
    def wrap_node(*args, **kwargs) -> Callable:
        name = func.__name__
        sig = signature(func)
        inputs = [(k,v.annotation) for k,v in sig.parameters.items()]
        o = sig.return_annotation
        if o is not None:
            outputs = type[o]
        else:
            outputs = None
        return Node(func=func, name=name, inputs=inputs, outputs=outputs)

    return wrap_node

@node
async def test_(obj_to_print: str) -> None:
    return

@node
async def test_i(obj_to_print = 0) -> int:
    return obj_to_print

@node
async def test_o_i(obj_to_print: int) -> Optional[int]:
    return obj_to_print

@node
async def test_o_d_s_s(obj_to_print: Dict[str,str]) -> Optional[Dict[str,str]]:
    return obj_to_print

@node
async def test_o_d_s_t_s_i(obj_to_print: Dict[str,Tuple[str,int]]) -> Optional[Dict[str,Tuple[str,int]]]:
    return obj_to_print



async def main():
    a = test_()
    print(a.name)
    print(a.inputs)
    print(a.outputs)
    b = test_i()
    print(b.name)
    print(b.inputs)
    print(b.outputs)
    c = test_o_i()
    print(c.name)
    print(c.inputs)
    print(c.outputs)
    d = test_o_d_s_s()
    print(d.name)
    print(d.inputs)
    print(d.outputs)
    e = test_o_d_s_t_s_i()
    print(e.name)
    print(e.inputs)
    print(e.outputs)


if sys.version_info >= (3, 11):
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())
else:
    uvloop.install()
    asyncio.run(main())
