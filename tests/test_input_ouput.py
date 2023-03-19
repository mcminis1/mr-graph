import pytest
from mr_graph.graph import Graph
from functions import sub_1, add_1, reverse_order, mult_2


@pytest.mark.asyncio
async def test_input_inference():
    # explicit input ordering based on func name + args in case of name conflicts
    g = Graph()
    g.add_nodes([sub_1, add_1, reverse_order])

    # this need to be named according to the func inputs
    o_1 = g.sub_1()
    o_2 = g.add_1()
    g.outputs = g.reverse_order(o_1, o_2)

    v = await g(5, 6)
    assert v.s == 4
    assert v.t == 7

@pytest.mark.asyncio
async def test_split_inputs():
    # explicit input ordering based on func name + args in case of name conflicts
    g = Graph()
    g.add_nodes([sub_1, add_1, reverse_order])

    # this need to be named according to the func inputs
    o_0 = g.sub_1()
    o_1 = g.add_1()
    o_2 = g.reverse_order(o_0, o_1)
    g.outputs  = g.add_1(o_2.t)

    v = await g(5,5)
    assert v.m == 7
