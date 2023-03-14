import pytest
from mr_graph.graph import Graph
from functions import add_to_point, Point, split_point, add_1


@pytest.mark.asyncio
async def test_add_to_point_kwds():
    # explicit defined linear example
    g = Graph(nodes=[add_to_point])

    sample_point = Point(x=1, y=1)
    o_1 = g.input(name="p")
    g.outputs = g.add_to_point(o_1)
    v = await g(p=sample_point)
    assert v.p.x == 2
    assert v.p.y == 2


@pytest.mark.asyncio
async def test_add_to_point_args():
    # explicit defined linear example
    g = Graph(nodes=[add_to_point])

    sample_point = Point(x=1, y=1)
    g.outputs = g.add_to_point()
    v = await g(sample_point)
    assert v.p.x == 2
    assert v.p.y == 2


@pytest.mark.asyncio
async def test_add_to_point_split():
    # explicit defined linear example
    g = Graph(nodes=[add_to_point, split_point, add_1])

    sample_point = Point(x=1, y=1)
    p1 = g.add_to_point()
    p2 = g.split_point(p1)
    g.outputs = g.add_1(p2)
    v = await g(sample_point)
    assert v.m == 3


@pytest.mark.asyncio
async def test_add_to_point_split_2():
    # explicit defined linear example
    g = Graph(nodes=[add_to_point, split_point, add_1])

    sample_point = Point(x=1, y=2)
    p1 = g.add_to_point()
    p2 = g.split_point(p1, field="y")
    g.outputs = g.add_1(p2)
    v = await g(o=sample_point)
    assert v.m == 4
