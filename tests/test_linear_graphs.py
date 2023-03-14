import pytest
from mr_graph.graph import Graph
from functions import sub_1, add_1, mult_2, return_one


@pytest.mark.asyncio
async def test_explicit_linear():
    # explicit defined linear example
    g = Graph(nodes=[sub_1, return_one, mult_2])

    o_1 = g.return_one()
    o_2 = g.sub_1(o_1)
    g.outputs = g.mult_2(o_2)
    v = await g()
    assert v.q == 0


@pytest.mark.asyncio
async def test_implicit_linear():
    # using the names, it figures out what path to chart through the functions
    g = Graph(nodes=[return_one, sub_1, mult_2])
    # this will wire it up as sub_1 -> add_1 -> mult_2 using the input/output names
    # no ambiguity in the input, pass as arg
    v = await g()
    assert v.q == 0


@pytest.mark.asyncio
async def test_implicit_linear_arg():
    # using the names, it figures out what path to chart through the functions
    g = Graph()
    g.add_nodes([sub_1, add_1, mult_2])
    # this will wire it up as sub_1 -> add_1 -> mult_2 using the input/output names
    # no ambiguity in the input, pass as arg
    v = await g(5)
    assert v.q == 10


@pytest.mark.asyncio
async def test_implicit_linear_named():
    # using the names, it figures out what path to chart through the functions
    g = Graph(nodes=[sub_1, add_1, mult_2])
    # this will wire it up as sub_1 -> add_1 -> mult_2 using the input/output names
    # no ambiguity in the input, pass as arg
    # we could pass in explicitly to the graph
    v = await g(n=5)
    assert v.q == 10
