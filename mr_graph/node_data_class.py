from pydantic import BaseModel, Extra, Field
import typing


class NodeDataClass(BaseModel):
    """The baseclass for dataclasses generated during graph execution.

    Args:
        BaseModel: Pydantic basemodel

    Raises:
        Exception: Raised when adding two NodeDataClass with the same attr name.
        Exception: Raised when adding a NodeDataClass to a non-NodeDataClass.
        Exception: Raised when iadd-ing a NodeDataClass to a non-NodeDataClass.

    Returns:
        NodeDataClass: returns self. The result of + or += methods.
    """

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    def __add__(self, other) -> "NodeDataClass":
        """adding two NodeDataClass together.
        todo: make more intuitive.

        Args:
            other (NodeDataClass): other to add to self

        Raises:
            Exception: Raised when adding two NodeDataClass with the same attr name
            Exception: Raised when adding a NodeDataClass to a non-NodeDataClass

        Returns:
            NodeDataClass: All attrs are added to self and returned as the result of +.
        """
        if isinstance(other, NodeDataClass):
            for attr, val in other.__dict__.items():
                if attr in ["_Graph__node_name", "__node_name"]:
                    continue
                elif attr in self.__dict__ and getattr(self, attr) == None:
                    setattr(self, attr, val)
                elif attr not in self.__dict__:
                    setattr(self, attr, val)
                else:
                    raise Exception(
                        f"Attempting to overwrite {attr} when adding NodeDataClass"
                    )
            return self
        else:
            raise Exception("Adding a not NodeDataClass to a NodeDataClass")

    def __iadd__(self, other):
        """Result of += operation with another NodeDataClass
        todo: make more intuitive.

        Raises:
            Exception: Raised when iadd-ing a NodeDataClass to a non-NodeDataClass

        Returns:
            list: Each NodeDataClass is appended to a list and returned.
        """
        if isinstance(other, NodeDataClass):
            for attr, val in other.__dict__.items():
                if attr in ["_Graph__node_name", "__node_name"]:
                    continue
                elif attr in self.__dict__ and getattr(self, attr) == None:
                    setattr(self, attr, val)
                elif attr not in self.__dict__:
                    setattr(self, attr, val)
                else:
                    raise Exception(
                        f"Attempting to overwrite {attr} when adding NodeDataClass"
                    )
            return self
        else:
            raise Exception("Adding a not NodeDataClass to a NodeDataClass")


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
"""dict: module level map for typing strings to annotation strings
"""


def parse_annotation(class_str: str) -> str:
    """parse the annotation string and return a type definition.

    Args:
        class_str (str): Generated using str(type( x )).

    Returns:
        str: Annotation for dataclass
    """
    class_name = class_str
    if class_str.startswith("<class '"):
        class_name = class_str[8:-2]
    elif class_str.startswith("<function "):
        class_name = class_str.split(" ")[1]
    if class_name in type_map:
        return type_map[class_name]
    return class_name


def parse_doc(func: typing.Callable) -> list[typing.Optional[tuple[str, str]]]:
    """Parses the doctrings for functions (__doc__) to get the name and type of returned values.

    Args:
        func (typing.Callable): function to get return values for.

    Returns:
        list[typing.Optional[tuple[str, str]]]: list of string tuples. Tuples contain the name and type of the return values used to create new dataclasses.
    """
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


def parse_default(parm: str) -> typing.Optional[str]:
    """Determine the default value for a function parameter.

    Args:
        parm (str): parameter string

    Returns:
        typing.Optional[str]: Parameter's default value.
    """
    parts = parm.split("=")
    if len(parts) == 1:
        return None
    else:
        return parts[1].strip("' ")
