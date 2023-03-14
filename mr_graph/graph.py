import asyncio
import typing
import logging
from uuid import uuid4 as uuid
from pydantic import Field
from mr_graph.node import build_node, NODE_TYPES, NodeDataClass
from dataclasses import make_dataclass, fields, asdict
from inspect import iscoroutinefunction
from functools import partial


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


class Graph:
    nodes: dict[str, NODE_TYPES] = dict()
    flow: dict[str, GraphIO] = dict()
    inputs: dict[str, NodeDataClass] = dict()
    outputs: NodeDataClass = None

    def __init__(self, nodes: typing.List[typing.Callable] = []):
        super().__init__()
        self.nodes = dict()
        self.flow = dict()
        self.inputs = dict()
        self.outputs = None
        self.add_nodes(nodes)

    def add_node(self, func: typing.Callable):
        node = build_node(func)
        self.nodes[node.name] = node

        gio = partial(self.__node_wrapper, node)
        setattr(self, node.name, gio)

    def add_nodes(self, funcs: typing.List[NODE_TYPES]):
        if funcs is not None:
            for func in funcs:
                self.add_node(func)

    def __plan_implicit_graph_flow(self):
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
        if len(self.flow.keys()) == 0:
            # implicit graph definition
            self.__plan_implicit_graph_flow()

        intermediate_results = dict()
        if len(args) == len(self.inputs):
            for arg, (key, val) in zip(args, self.inputs.items()):
                if isinstance(arg, NodeDataClass):
                    # if the arg is a dataclass, then we use it to set the input dataclass
                    arg_fields = sorted([x.name for x in fields(arg)])
                    input_fields = sorted([x.name for x in fields(val)])
                    if arg_fields == input_fields:
                        for input_field in input_fields:
                            setattr(val, input_field, getattr(arg, input_field))
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
            ran_1 = False
            running_coroutines = {}
            for step_name, step_graphio in self.flow.items():
                ready_to_run = True
                step_kwds = dict()
                for input_kwd, (
                    input_node_id,
                    input_node_kwd,
                ) in step_graphio.inputs.items():
                    if (
                        asdict(intermediate_results[input_node_id])[input_node_kwd]
                        is None
                    ):
                        ready_to_run = False
                    else:
                        step_kwds[input_kwd] = asdict(
                            intermediate_results[input_node_id]
                        )[input_node_kwd]
                if ready_to_run and step_graphio.name not in completed_tasks:
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
                    completed_tasks.append(step_graphio.name)
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

        if isinstance(self.outputs, list):
            combined_dataclass = self.outputs[0]
            for output in self.outputs[1:]:
                combined_dataclass = combined_dataclass + output
            return combined_dataclass
        return self.outputs

    def __node_wrapper(self, node: NODE_TYPES, *args, **kwds) -> NodeDataClass:
        name = str(node.name) + "-" + str(uuid())
        node_input_dataclass = node.inputs()
        node_input_fields = [x.name for x in fields(node_input_dataclass)]
        input_mapping = dict()

        for indx, arg in enumerate(args):
            if isinstance(arg, NodeDataClass):
                arg_node_name = arg.__node_name
                arg_node_fields = fields(arg)
                for arg_node_field in arg_node_fields:
                    input_key = (arg_node_name, arg_node_field.name)
                    input_mapping[node_input_fields[indx]] = input_key
            # else:
            # # eventually we need to allow splitting NodeDataClass and
            # # using individual fields as inputs in later graphs

        for kwd, dc in kwds.items():
            if kwd in node_input_fields:
                if isinstance(dc, NodeDataClass):
                    input_mapping[kwd] = (dc.__node_name, fields(dc)[0])
                else:
                    # some constant passed
                    i = self.input(name=kwd, default_value=dc)
                    input_mapping[kwd] = (i.__node_name, kwd)
        if len(node_input_fields) != len(input_mapping.keys()):
            missing_fields = [
                x for x in node_input_fields if x not in list(input_mapping.keys())
            ]
            defaults_exist = True
            for missing_field in missing_fields:
                if getattr(node_input_dataclass, missing_field) is None:
                    defaults_exist = False
            if not defaults_exist:
                i = self.input(names=missing_fields)
                for field in missing_fields:
                    input_mapping[field] = (i.__node_name, field)

        o = node.outputs()
        o.__node_name = name
        self.flow[name] = GraphIO(name=name, inputs=input_mapping, node=node, output=o)
        return o

    def input(
        self, names: list[str] = [], name: str = None, default_value: typing.Any = None
    ) -> NodeDataClass:
        new_node_name = str(uuid())
        input_dataclass = None
        if name is None:
            input_dataclass = make_dataclass(
                f"graph_input_{new_node_name}",
                [
                    (
                        name,
                        "typing.Optional[typing.Any]",
                        Field(default=None, init=False),
                    )
                    for name in names
                ],
                bases=(NodeDataClass,),
                init=False,
            )
        else:
            input_dataclass = make_dataclass(
                f"graph_input_{new_node_name}",
                [
                    (
                        name,
                        "typing.Optional[typing.Any]",
                        Field(default=default_value, init=False),
                    )
                ],
                bases=(NodeDataClass,),
                init=False,
            )
        i = input_dataclass()
        i.__node_name = new_node_name
        self.inputs[new_node_name] = input_dataclass()
        return i
