import typing
from statistics import mean

Point = typing.NamedTuple("Point", [("x", int), ("y", int)])


def return_one():
    """
    return 1

    return one with no inputs

    Returns
    -------
    m : float
        equal to 1
    """
    return 1


async def add_1(n: float):
    """
    add 1 to a number

    add 1 to the input value n.

    Parameters
    ----------
    n : float
        number to add 1 to.

    Returns
    -------
    m : float
        equal to n + 1
    """
    return n + 1


async def add_to_tuple1(o: tuple[int, int]):
    """
    add 1 to numbers in a tuple

    add 1 to numbers in a tuple

    Parameters
    ----------
    o : float
        number to add 1 to.

    Returns
    -------
    p : tuple[int,int]
        input tuple with 1 added
    """
    return o[0] + 1, o[1] + 1


async def split_point(pnt: Point, field: str = "x"):
    """
    pull a field off a point

    either x or y. pull a field off the point objext

    Parameters
    ----------
    pnt : Point
        the point
    field : str
        the attribute to pull. either x or y

    Returns
    -------
    p_field : int
        the output p.field
    """
    return getattr(pnt, field)


async def add_to_point(o: Point):
    """
    add 1 to numbers in a Point

    add 1 to numbers in a Point

    Parameters
    ----------
    o : Point
        Point to add 1 to.

    Returns
    -------
    p : Point
        input Point with 1 added
    """
    p = Point(x=o.x + 1, y=o.y + 1)
    return p


async def sub_1(m: int):
    """
    subtract 1 from a number

    subtract 1 from the input value m.

    Parameters
    ----------
    m : float
        number to subtract 1 to.

    Returns
    -------
    p : float
        equal to n - 1
    """
    return m - 1


async def sub_dict_1(j: dict[str, int]):
    """
    subtract 1 from a number

    subtract 1 from the input value m.

    Parameters
    ----------
    j : dict[str, int]
        dict to sub 1 to.

    Returns
    -------
    p : dict[str, int]
        dict to - 1
    """
    p = dict()
    for k, v in j.items():
        p[k] = v - 1
    return p


# we can mix async and sync calls in a graph
def mult_2(p: float):
    """
    multiply a number by 2

    returns p*2

    Parameters
    ----------
    p : float
        number to multiply by 2

    Returns
    -------
    q : float
        equal to p * 2
    """
    return 2 * p


def add_n_m(n: float, m: float):
    """
    add two numbers together

    q = m + n

    Parameters
    ----------
    m : float
        number to add to n.
    n : float
        number to add to m.

    Returns
    -------
    r : float
        equal to m + n
    """
    return m + n


# multiple outputs are OK. if you don;t want it to be a tuple.
# you can split the output into the two named outputs
def div_mul_2(n: float):
    """
    divide by 2 and multiple by 2

    s = n/2 and t = n*2

    Parameters
    ----------
    n : float
        number to operate on

    Returns
    -------
    s : float
        equal to n/2
    t : float
        equal to n*2
    """
    return n / 2, 2 * n


def reverse_order(s: float, t: float):
    """
    return reversed order

    s <-> t

    Parameters
    ----------
    s : float
        number to swap with b
    t : float
        number to swap with a

    Returns
    -------
    t : float
        equal to b
    s : float
        equal to a
    """
    return t, s


async def average_list(list_of_ints: list[int]):
    """
    return average of a list

    Parameters
    ----------
    list_of_ints : list[float]
        list of values

    Returns
    -------
    avg : float
        average of the list
    """
    return mean(list_of_ints)
