from mr_graph.node import NODE_TYPES, NodeDataClass


class GraphIO:
    name: str
    inputs: dict[str, tuple[str, str]]  # keys to pull input
    node: NODE_TYPES
    output: NodeDataClass

    def __init__(self, name, inputs, node, output):
        self.name = name
        self.inputs = inputs
        self.node = node
        self.output = output
