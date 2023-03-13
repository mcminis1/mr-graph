import pytest
from graph_flow.graph import Graph
from functions import sub_1, add_1, reverse_order


@pytest.mark.asyncio
async def test_fan_in():
    # explicit input ordering based on func name + args in case of name conflicts
    g = Graph()
    g.add_nodes([sub_1, add_1, reverse_order])

    i0 = g.input(name="m")
    i1 = g.input(name="n")
    o_1 = g.sub_1(i0)
    o_2 = g.add_1(i1)

    g.outputs = g.reverse_order(o_1, o_2)

    v = await g(m=5, n=6)

    print(v)
    assert v.s == 4
    assert v.t == 7
