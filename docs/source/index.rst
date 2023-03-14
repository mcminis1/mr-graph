.. graph-flow documentation master file, created by
   sphinx-quickstart on Tue Mar 14 12:18:54 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.





Graph-Flow
==========

Welcome to Graph Flow!

Graph-Flow is a python library designed to make composing graphs of sync and async functions easy!

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   ./getting_started/installation
   ./getting_started/starter_examples


Features
--------
Graph flow is new and under active development. Current Features include.

* Use with either async or sync functions
* Uses regular documentation formats to name return values.
* Can infer pipelines from input and output signatures
* All directed acyclic graph layouts supported. linear, fan-in, fan-out.

If you're interested in contributing, please create a ticket on `github`_ and suggest a feature!

.. _github: https://github.com/mcminis1/graph-flow

Example Usage
-------------

Building graphs can be as easy as::

   from graph_flow import Graph

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
      
   async def add_1(m: float):
      """
      add 1 to a number

      add 1 to the input value m.

      Parameters
      ----------
      n : float
         number to add 1 to.

      Returns
      -------
      n : float
         equal to n + 1
      """
      return n + 1

   async def build_implicit_linear_graph():
      """
      Return 2

      Simple example linear graph. Wired up automagically using the input and output variable names.

      Parameters
      ----------
      
      Returns
      -------
      two : float
         always equal to 2
      """

      g = Graph(nodes=[return_one, add_1])
      return await g()




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
