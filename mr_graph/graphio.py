from mr_graph.node import NODE_TYPES, NodeDataClass
from uuid import uuid4 as uuid
from dataclasses import fields, asdict
import logging
from mr_graph.node_data_tracker import NodeDataTracker
from mr_graph.node_data_aggregator import NodeDataAggregator

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
    missing_fields: list[str] = list()

    def __init__(self, node, args, kwds):
        self.node = node
        self.name = str(node.name) + "-" + str(uuid())
        self.inputs = dict()
        self.missing_fields = list()

        o = node.outputs()
        setattr(o, "__node_name", self.name)
        self.output = o

        node_input_dataclass = node.inputs()
        node_input_fields = [x.name for x in fields(node_input_dataclass)]

        for indx, arg in enumerate(args):
            if isinstance(arg, NodeDataTracker):
                # we assume a mapping from args order to function input order
                arg_node_name = getattr(arg.data_class, "__node_name")
                arg_node_fields = fields(arg.data_class)
                for arg_node_field in arg_node_fields:
                    input_key = (arg_node_name, arg_node_field.name)
                    self.inputs[node_input_fields[indx]] = input_key
            elif isinstance(arg, tuple) and arg[0] == "mr_graph_node":
                (_, key, val) = arg
                self.inputs[node_input_fields[indx]] = (key, val)

        for kwd, dc in kwds.items():
            if kwd in node_input_fields:
                if isinstance(dc, NodeDataTracker):
                    self.inputs[kwd] = (getattr(dc, "__node_name"), kwd)
                elif isinstance(dc, NodeDataAggregator):
                    self.inputs[kwd] = (getattr(dc, "__node_name"), getattr(dc, "result_name"))
                elif isinstance(dc, tuple) and dc[0] == "mr_graph_node":
                    (_, key, val) = dc
                    self.inputs[node_input_fields[indx]] = (key, val)
                else:
                    # some constant passed
                    self.inputs[kwd] = (None, dc)

        if len(node_input_fields) != len(self.inputs.keys()):
            candidate_fields = [
                x for x in node_input_fields if x not in list(self.inputs.keys())
            ]
            for candidate_field in candidate_fields:
                if getattr(node_input_dataclass, candidate_field) is None:
                    self.missing_fields.append(candidate_field)

        if len(self.missing_fields) > 0:
            logging.warning(
                f"unmapped inputs node:({node.name}) missing:{self.missing_fields}"
            )

    def add_input(self, field, input):
        self.inputs[field] = (getattr(input, "__node_name"), field)
