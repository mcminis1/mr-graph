from mr_graph.node import NODE_TYPES, NodeDataClass


class GraphIO:
    """Input and output tracker for a node in the graph.

    Attributes:
        name (str): Unique name for tracking use.
        inputs (dict[str, tuple[str, str]]): The input for this node's function.
        node (NODE_TYPES): The function to consume input and return output.
        output (NodeDataClass): The output for this node in the graph.

    """

    name: str
    inputs: dict[str, tuple[str, str]]  # keys to pull input
    node: NODE_TYPES
    output: NodeDataClass

    def __init__(self, name, inputs, node, output):
        self.name = name
        self.inputs = inputs
        self.node = node
        self.output = output
