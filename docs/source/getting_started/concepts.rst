Concepts
===============

Mr. Graph consists of 3 kinds of entities:

1. Graphs
2. Nodes
3. NodeDataClass

Graphs
------
A Graph is an entity that works like a function. To build a graph you must add functions to it. Once you've added functions to it, they are converted to nodes and can be organized into an execution graph. If you've chosen to name your inputs and outputs according to convention (as described in the tutorial), you may not need to organize the graph before executing.

Nodes
-----
A wrapper for a function that's used to track the input and outputs from a function as it's called throughout the graph.

The convention used throughout Mr. Graph is that you can use google docstrings to name your outputs from functions. This allows them to be tracked and ordering functions can be done by just looking at input and output names and types.

NodeDataClass
-------------
The dataclasses used as input and output from the functions in the graph.
