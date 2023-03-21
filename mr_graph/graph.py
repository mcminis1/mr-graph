import asyncio
import typing
import logging
from uuid import uuid4 as uuid
from pydantic import Field
from mr_graph.node import build_node, NODE_TYPES
from mr_graph.node_data_class import NodeDataClass
from mr_graph.node_data_tracker import NodeDataTracker
from mr_graph.node_data_aggregator import NodeDataAggregator
from dataclasses import make_dataclass, fields, asdict
from inspect import iscoroutinefunction
from functools import partial
from mr_graph.graphio import GraphIO


class Graph:
    """Execution graph class

    Attributes:
        nodes (dict[str, NODE_TYPES]): Graph nodes.
        flow (dict[str, GraphIO]): Inputs, nodes, and outputs for all of the nodes defined in the graph.
        inputs (dict[str, NodeDataClass]): The inputs required by the graph.
        outputs (NodeDataClass): The outputs from all defined outputs in the graph.

    Returns:
        NodeDataClass: outputs from the functions used in the graph.
    """

    nodes: dict[str, NODE_TYPES] = dict()
    flow: dict[str, GraphIO] = dict()
    inputs: dict[str, NodeDataClass] = dict()
    outputs: NodeDataClass = None

    def __init__(self, nodes: typing.List[typing.Callable] = []):
        """Graphs can be initialized by passing nodes, or defined later.

        Args:
            nodes (typing.List[typing.Callable], optional): Functions which are to be converted into graph nodes. Defaults to [].
        """
        super().__init__()
        self.nodes = dict()
        self.flow = dict()
        self.inputs = dict()
        self.outputs = None
        self.add_nodes(nodes)

    def add_node(self, func: typing.Callable):
        """generates a node from a function

        Args:
            func (typing.Callable): builds the node
        """
        node = build_node(func)
        self.nodes[node.name] = node

        # THe graph adds an attribute that tracks the use of the function, its input, and its ouput
        gio = partial(self.__node_wrapper, node)
        setattr(self, node.name, gio)

    def add_nodes(self, funcs: typing.List[NODE_TYPES]):
        """adds a list of functions as nodes

        Args:
            funcs (typing.List[NODE_TYPES]): iterate over functions and adds each.
        """
        if funcs is not None:
            for func in funcs:
                self.add_node(func)

    def __plan_implicit_graph_flow(self):
        """Use the function input and output names to generate the graph topology."""
        graph_edges = []
        nodes_with_inputs = set()
        leaf_nodes = set(self.nodes.keys())
        for node_name_0, node_0 in self.nodes.items():
            if len(fields(node_0.inputs)) == 0:
                # always a root
                graph_edges.append((node_name_0, None, None))
            else:
                for node_name_1, node_1 in self.nodes.items():
                    node_0_inputs = sorted([x.name for x in fields(node_0.inputs)])
                    node_1_outputs = sorted([x.name for x in fields(node_1.outputs)])
                    if node_name_0 != node_name_1:
                        if node_0_inputs == node_1_outputs:
                            # node_1 is the input to node_0
                            graph_edges.append(
                                (node_name_0, node_name_1, node_1_outputs)
                            )
                            nodes_with_inputs.add(node_name_0)
                            if node_name_1 in leaf_nodes:
                                leaf_nodes.remove(node_name_1)
        # find global inputs.
        root_node_names = [
            x for x in list(self.nodes.keys()) if x not in nodes_with_inputs
        ]
        outputs = {}
        for root_node_name in root_node_names:
            # we get the outputs for the root nodes and then
            # iterate over the rest until all the edges have inputs.
            self_root_node = getattr(self, root_node_name)
            outputs[root_node_name] = self_root_node()
        while len(graph_edges) > 0:
            remaining_edges = []
            for graph_edge in graph_edges:
                if graph_edge[1] is None:
                    # no input node
                    self_node = getattr(self, graph_edge[0])
                    outputs[graph_edge[0]] = self_node()
                elif graph_edge[1] in list(outputs.keys()):
                    self_node = getattr(self, graph_edge[0])
                    outputs[graph_edge[0]] = self_node(outputs[graph_edge[1]])
                else:
                    remaining_edges.append(graph_edge)
            graph_edges = remaining_edges

        self.outputs = [outputs[x] for x in leaf_nodes]
        if len(self.outputs) == 1:
            self.outputs = self.outputs[0]

    async def __call__(self, *args, **kwds) -> dict[str, NodeDataClass]:
        """Execute the graph. If the graph has not been configured, use inputs/outputs to plan the graph.

        Returns:
            dict[str, NodeDataClass]: The output from the graph.
        """
        if len(self.flow.keys()) == 0:
            # implicit graph definition
            self.__plan_implicit_graph_flow()

        intermediate_results = dict()
        if len(args) == len(self.inputs):
            for arg, (key, val) in zip(args, self.inputs.items()):
                if isinstance(arg, NodeDataTracker):
                    # if the arg is a dataclass, then we use it to set the input dataclass
                    arg_fields = sorted(arg.fields)
                    input_fields = sorted([x.name for x in fields(val)])
                    if arg_fields == input_fields:
                        for input_field in input_fields:
                            setattr(
                                val, input_field, getattr(arg.data_class, input_field)
                            )
                        intermediate_results[key] = val
                elif isinstance(arg, tuple) and arg[0] == "mr_graph_node":
                    (_, key, val) = arg
                    intermediate_results[key] = val
                else:
                    # if the arg is not a dataclass, we use the value to set the values in order.
                    # each input must be a single value
                    input_fields = [x.name for x in fields(val)]
                    setattr(val, input_fields[0], arg)
                    intermediate_results[key] = val
        else:
            # number of args does not match. we use kwargs now.
            for g_input_name, g_input_dataclass in self.inputs.items():
                # here we check the input fields
                g_input_dc_field_name = fields(g_input_dataclass)
                if g_input_dc_field_name[0].name in kwds.keys():
                    #  if the keywords match, use the keyword
                    setattr(
                        g_input_dataclass,
                        g_input_dc_field_name[0].name,
                        kwds[g_input_dc_field_name[0].name],
                    )
                intermediate_results[g_input_name] = g_input_dataclass

        for node_name, node in self.flow.items():
            # these are the outputs for the flow nodes
            intermediate_results[node_name] = node.output

        ran_1 = True
        completed_tasks = []
        while ran_1:
            # We iterate over all of the nodes and run any that are ready to be ran.
            # If we find that no more nodes can be executed, we quit.
            # todo: add WARNING if some nodes are not executed.
            # todo: add limits in case of loops
            ran_1 = False
            running_coroutines = {}
            for step_name, step_graphio in self.flow.items():
                step_kwds = self._check_if_ready_to_run(intermediate_results, step_graphio.inputs)
                if step_kwds is not None and step_graphio.name not in completed_tasks:
                    ran_1 = True
                    if iscoroutinefunction(step_graphio.node.func):
                        running_coroutines[step_graphio.name] = asyncio.create_task(
                            step_graphio.node(**step_kwds)
                        )
                    else:
                        step_evaluation = step_graphio.node(**step_kwds)
                        ks = list(asdict(intermediate_results[step_name]).keys())
                        if len(ks) > 1:
                            for i, k in enumerate(ks):
                                setattr(
                                    intermediate_results[step_graphio.name],
                                    str(k),
                                    step_evaluation[i],
                                )
                        else:
                            setattr(
                                intermediate_results[step_graphio.name],
                                str(ks[0]),
                                step_evaluation,
                            )
                        completed_tasks.append(step_name)
            coros = list(running_coroutines.values())
            if len(coros) > 0:
                await asyncio.gather(*coros)
                for step_name, step_evaluation in running_coroutines.items():
                    step_value = step_evaluation.result()
                    ks = list(asdict(intermediate_results[step_name]).keys())
                    if len(ks) > 1:
                        for i, k in enumerate(ks):
                            setattr(
                                intermediate_results[step_name], str(k), step_value[i]
                            )
                    else:
                        setattr(intermediate_results[step_name], str(ks[0]), step_value)
                    completed_tasks.append(step_name)

        for node, field in self.outputs.field_map.items():
            setattr(
                self.outputs.data_class,
                field,
                getattr(intermediate_results[node], field),
            )
        return self.outputs.data_class

    def __node_wrapper(self, node: NODE_TYPES, *args, **kwds) -> NodeDataTracker:
        """Wraps the node entity to enable tracking inputs and outputs.

        Args:
            node (NODE_TYPES): The node to be wrapped.

        Returns:
            NodeDataTracker: Output from node.
        """
        gio = GraphIO(node, args, kwds)
        if len(gio.missing_fields) > 0:
            for field in gio.missing_fields:
                i = self.input(name=field)
                gio.add_input(field=field, input=i)
                logging.warning(f"Adding inputs node:({gio.name}) missing:{field}")

        self.flow[gio.name] = gio
        return NodeDataTracker(gio.output)

    def input(
        self,
        name: str = None,
        d_type: str = "typing.Any",
        default_value: typing.Any = None,
    ) -> NodeDataTracker:
        """Generate a new dataclass input to the graph.

        Args:
            names (list[str], optional): attrs for the dataclass. Defaults to [].
            name (str, optional): attr (in case there is only one attr). Defaults to None.
            default_value (typing.Any, optional): Default value for the attr when functions have defaults. Defaults to None.

        Returns:
            NodeDataTracker: Dataclass for the input.
        """
        new_node_name = f"graph_input_{str(uuid())}"
        input_dataclass = make_dataclass(
            new_node_name,
            [
                (
                    name,
                    f"typing.Optional[{d_type}]",
                    Field(default=default_value, init=False),
                )
            ],
            bases=(NodeDataClass,),
            init=False,
        )
        i = input_dataclass()
        setattr(i, "__node_name", new_node_name)
        self.inputs[new_node_name] = i
        return NodeDataTracker(i)

    def aggregator(self, name: str):
        nda = NodeDataAggregator(name)
        self.flow[nda.name] = nda
        return nda




    def _check_if_ready_to_run(self, cached_results, input_dict) -> typing.Optional[dict[str, tuple[str, str]]]:
        step_kwds = dict()
        for input_kwd, (input_node_id, input_node_kwd) in input_dict.items():
            print(f"{input_kwd} ++{input_node_id} ++{input_node_kwd}")
            if input_node_id is not None and (
                asdict(cached_results[input_node_id])[input_node_kwd]
                is None
            ):
                return None
            elif input_node_id is None:
                if isinstance(input_node_kwd, NodeDataAggregator):
                    node_agg_data = self._check_if_ready_to_run(cached_results, input_node_kwd.inputs)
                    if len(node_agg_data) > 0:
                        step_kwds[input_kwd] = input_node_kwd(node_agg_data)
                    else:
                        return None
                elif isinstance(input_node_kwd, NodeDataTracker):
                    if len(input_node_kwd.fields) == 1:
                        node_name = getattr(input_node_kwd, '__node_name')
                        field = input_node_kwd.fields[0]
                        v = asdict(input_node_kwd[node_name])[field]
                        if v is not None:
                            step_kwds[input_kwd] = v
                        else:
                            return None
                else:
                    step_kwds[input_kwd] = input_node_kwd
            else:
                step_kwds[input_kwd] = asdict(
                    cached_results[input_node_id]
                )[input_node_kwd]
        return step_kwds