Tutorial
========

In these short sections you'll learn how to build and execute graphs using Mr. Graph.

Defining Functions
------------------
You can use blocking or async function in Mr. Graph. If you are already using google style docstrings all you need to change to take advantage of Mr. Graph is naming your outputs.


A blocking example with no inputs. ::

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

An async example that has an input and output.::

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


Implicit Graph Definition
-------------------------
As demonstrated in the root quickstart, you can wire up graphs implicitly ::

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

This method will return a dataclass with an attribute named 'm' (determined by the output annotation on the add_1 method).

Explicit Graph Definition
-------------------------
For more complex graphs it's sometimes required to wire them up manually. ::

   async def build_explicit_linear_graph():
      """
      Return 2

      Simple example linear graph. Wired up manually.

      Parameters
      ----------
      
      Returns
      -------
      two : float
         always equal to 2
      """

      g = Graph(nodes=[return_one, add_1])
      o_1 = g.return_one()
      g.outputs = g.sub_1(o_1)
      return await g()

In this case the return from `build_explicit_linear_graph` is the same as previously demonstrated in the implicit example; a dataclass with a single attribute named 'm'. If you inspect g.outputs you'll find that it's a dataclass with a single attribute named 'm' and is equal to None until the graph is executed.


Defining Graph Inputs
---------------------

We can define an input for the graph, and then pass in a value to it when executing it. ::

   async def pass_input_to method(input_val: int):
      """
      Return input_val + 1

      Simple example linear graph. pass in value and get value + 1 back.

      Parameters
      ----------
      
      Returns
      -------
      m : float
         equal to input_val + 1
      """

      g = Graph(nodes=[add_1])
      i_0 = g.input(name="n")
      g.outputs = g.add_1(i_0)
      return await g(n=input_val)

Alternatively, in this case, there would be no ambiguity if you passed in the `input_val` as an arg instead of a keyword arg. :: 

   async def pass_input_to method(input_val: int):
    ...
      return await g(input_val)

In general, Mr. Graph tries to wire things up using names. However, when it's unambiguous, it is possible to rely on ordering.

Multiple Outputs
----------------

Sometimes you need to return multiple values from a graph. ::

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
        
    async def fan_out_graph(input_val: int):
        # fan out example
        g = Graph()
        g.add_nodes([sub_1, add_1, mult_2])

        i_0 = g.input(name="n")
        o_1 = g.add_1(i_0)
        g.outputs = g.mult_2(o_1) 
        g.outputs += g.sub_1(o_1)

        return await g(n=input_val)

This will return a dataclass with two attributes: `p` and `q`.::
    
    v = await fan_out_graph(2)
    assert v.q == 4
    assert v.p == 1

When returning multiple values they are combined into a single dataclass object and returned. If there are conflicting names on the dataclasses then it will raise an error.

Aggregating results
-------------------

Sometimes its useful to aggregate results from many different nodes into a list to pass to a function (fan-in architecture). There is a special class member that allows you to build those lists called an aggregator :: 

    llm = Graph(nodes=[get_structured_answer, summarize_answers])

    answers = llm.aggregator(name="answers")
    for question in questions:
        sa = llm.get_structured_answer(user_question=question)
        answers += sa.answer
    llm.outputs = llm.summarize_answers(answers=answers)

    v = await llm(answers)
    return v.summary

In this example a list of answers is aggregated and used as an input to another function.
