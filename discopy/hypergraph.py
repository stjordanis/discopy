# -*- coding: utf-8 -*-

"""
Hypergraph categories.

Note
----

**Spiders**

We can check spider fusion, i.e. special commutative Frobenius algebra.

>>> x, y, z = types("x y z")
>>> split, merge = Spider(1, 2, x), Spider(2, 1, x)
>>> unit, counit = Spider(0, 1, x), Spider(1, 0, x)

* (Co)commutative (co)monoid:

>>> assert unit @ Id(x) >> merge == Id(x) == Id(x) @ unit >> merge
>>> assert merge @ Id(x) >> merge == Id(x) @ merge >> merge
>>> assert Swap(x, x) >> merge == merge
>>> assert split >> counit @ Id(x) == Id(x) == split >> Id(x) @ counit
>>> assert split >> split @ Id(x) == split >> Id(x) @ split
>>> assert split >> Swap(x, x) == split

* Frobenius:

>>> assert split @ Id(x) >> Id(x) @ merge\\
...     == merge >> split\\
...     == Id(x) @ split >> merge @ Id(x)\\
...     == Spider(2, 2, x)

* Speciality:

>>> assert split >> merge == Spider(1, 1, x) == Id(x)

* Coherence:

>>> assert Spider(0, 1, x @ x) == unit @ unit
>>> assert Spider(2, 1, x @ x) == Id(x) @ Swap(x, x) @ Id(x) >> merge @ merge
>>> assert Spider(1, 0, x @ x) == counit @ counit
>>> assert Spider(1, 2, x @ x) == split @ split >> Id(x) @ Swap(x, x) @ Id(x)

**Snakes**

Special commutative Frobenius algebras imply compact-closedness, i.e.

* Snake equations:

>>> left_snake = lambda x: Cap(x, x.r) @ Id(x) >> Id(x) @ Cup(x.r, x)
>>> right_snake = lambda x: Id(x) @ Cap(x.r, x) >> Cup(x, x.r) @ Id(x)
>>> assert left_snake(x) == Id(x) == right_snake(x)
>>> assert left_snake(x @ y) == Id(x @ y) == right_snake(x @ y)

* Yanking (a.k.a. Reidemeister move 1):

>>> right_loop = lambda x: Id(x) @ Cap(x, x.r)\\
...     >> Swap(x, x) @ Id(x.r) >> Id(x) @ Cup(x, x.r)
>>> left_loop = lambda x: Cap(x.r, x) @ Id(x)\\
...     >> Id(x.r) @ Swap(x, x) >> Cup(x.r, x) @ Id(x)
>>> top_loop = lambda x: Cap(x, x.r) >> Swap(x, x.r)
>>> bottom_loop = lambda x: Swap(x, x.r) >> Cup(x.r, x)
>>> reidemeister1 = lambda x:\\
...     top_loop(x) == Cap(x.r, x) and bottom_loop(x) == Cup(x, x.r)\\
...     and left_loop(x) == Id(x) == right_loop(x)
>>> assert reidemeister1(x) and reidemeister1(x @ y) and reidemeister1(Ty())

* Coherence:

>>> assert Cap(x @ y, y @ x)\\
...     == Cap(x, x) @ Cap(y, y) >> Id(x) @ Swap(x, y @ y)\\
...     == Spider(0, 2, x @ y) >> Id(x @ y) @ Swap(x, y)
>>> assert Cap(x, x) >> Cup(x, x) == Spider(0, 0, x)

**Swaps**

We can also check that the axioms for symmetry hold on the nose.

* Involution (a.k.a. Reidemeister move 2):

>>> reidermeister2 = lambda x, y: Swap(x, y) >> Swap(y, x) == Id(x @ y)
>>> assert reidermeister2(x, y) and reidermeister2(x @ y, z)

* Yang-Baxter (a.k.a. Reidemeister move 3):

>>> left = Swap(x, y) @ Id(z)\\
...     >> Id(y) @ Swap(x, z)\\
...     >> Swap(y, z) @ Id(x)
>>> right = Id(x) @ Swap(y, z)\\
...     >> Swap(x, z) @ Id(y)\\
...     >> Id(z) @ Swap(x, y)
>>> assert left == right

* Coherence (a.k.a. pentagon equations):

>>> assert Swap(x, y @ z) == Swap(x, y) @ Id(z) >> Id(y) @ Swap(x, z)
>>> assert Swap(x @ y, z) == Id(x) @ Swap(y, z) >> Swap(x, z) @ Id(y)

* Naturality:

>>> f = Box("f", x, y)
>>> assert f @ Id(z) >> Swap(f.cod, z) == Swap(f.dom, z) >> Id(z) @ f
>>> assert Id(z) @ f >> Swap(z, f.cod) == Swap(z, f.dom) >> f @ Id(z)
"""

import random

import matplotlib.pyplot as plt
from networkx import Graph, connected_components, spring_layout, draw_networkx

from discopy import cat, monoidal, rigid
from discopy.cat import AxiomError
from discopy.drawing import Node, COLORS


class Ty(rigid.Ty):
    @staticmethod
    def upgrade(old):
        return Ty(*old.objects)

    @property
    def l(self):
        return Ty(*self.objects[::-1])

    r = l


def types(names):
    """ Transforms strings into lists of :class:`discopy.hypergraph.Ty`. """
    return map(Ty.upgrade, monoidal.types(names))



class Diagram(cat.Arrow):
    """
    Diagram in a hypergraph category.

    Parameters
    ----------

    dom : discopy.hypergraph.Ty
        Domain of the diagram.
    cod : discopy.hypergraph.Ty
        Codomain of the diagram.
    boxes : List[discopy.hypergraph.Box]
        List of :class:`discopy.symmetric.Box`.
    wires : List[Any]
        List of wires from ports to spiders.
    spider_types : Mapping[Any, discopy.hypergraph.Ty], optional
        Mapping from spiders to basic types, if :code:`None` then this is
        computed from the types of ports.

    Note
    ----

    The wires go from ports to spiders, they are given as a list of length::

        len(dom) + sum(len(box.dom) + len(box.cod) for box in boxes) + len(cod)

    The values themselves don't matter, they are simply labels for the spiders.
    We must have :code:`len(types) >= len(set(wires))`, the spiders that don't
    appear as the target of a wire are scalar spiders, i.e. with zero legs.

    Abstractly, a hypergraph diagram can be seen as a cospan for the boundary::

        range(len(dom)) -> range(n_spiders) <- range(len(cod))

    together with a cospan for each box in boxes::

        range(len(box.dom)) -> range(n_spiders) <- range(len(box.cod))

    Composition of two hypergraph diagram is given by the pushout of the span::

        range(self.n_spiders) <- range(len(self.cod)) -> range(other.n_spiders)

    Examples
    --------

    >>> x, y, z = types("x y z")

    >>> assert Id(x @ y @ z).n_spiders == 3
    >>> assert Id(x @ y @ z).wires == [0, 1, 2, 0, 1, 2]

    >>> assert Swap(x, y).n_spiders == 2
    >>> assert Swap(x, y).wires == [0, 1, 1, 0]

    >>> assert Spider(1, 2, x @ y).n_spiders == 2
    >>> assert Spider(1, 2, x @ y).wires == [0, 1, 0, 1, 0, 1]
    >>> assert Spider(0, 0, x @ y @ z).n_spiders == 3
    >>> assert Spider(0, 0, x @ y @ z).wires == []

    >>> f, g = Box('f', x, y), Box('g', y, z)

    >>> assert f.n_spiders == g.n_spiders == 2
    >>> assert f.wires == g.wires == [0, 0, 1, 1]

    >>> assert (f >> g).n_spiders == 3
    >>> assert (f >> g).wires == [0, 0, 1, 1, 2, 2]

    >>> assert (f @ g).n_spiders == 4
    >>> assert (f @ g).wires == [0, 1, 0, 2, 1, 3, 2, 3]
    """
    def __init__(self, dom, cod, boxes, wires, spider_types=None):
        super().__init__(dom, cod, boxes, _scan=False)
        if len(wires) != len(dom)\
                + sum(len(box.dom) + len(box.cod) for box in boxes) + len(cod):
            raise ValueError
        relabeling = list(sorted(set(wires), key=lambda i: wires.index(i)))
        wires = [relabeling.index(spider) for spider in wires]
        n_connected_spiders = len(relabeling)
        if spider_types is None:
            port_types = list(map(Ty, self.dom)) + sum(
                [list(map(Ty, box.dom @ box.cod)) for box in boxes], [])\
                + list(map(Ty, self.cod))
            spider_types = {}
            for spider, typ in zip(wires, port_types):
                if spider in spider_types:
                    if spider_types[spider] != typ:
                        raise AxiomError
                else:
                    spider_types[spider] = typ
            spider_types = [spider_types[i] for i in sorted(spider_types)]
        else:
            spider_types = {i: t for i, t in enumerate(spider_types)}\
                if isinstance(spider_types, list) else spider_types
            relabeling += list(sorted(set(spider_types) - set(relabeling)))
            spider_types = [spider_types[spider] for spider in relabeling]
        self._wires, self._spider_types = wires, spider_types
        self._n_spiders = len(spider_types)
        self._scalar_spiders = set(range(n_connected_spiders, self._n_spiders))

    @property
    def scalar_spiders(self):
        """ The zero-legged spiders in a hypergraph diagram. """
        return self._scalar_spiders

    @property
    def n_spiders(self):
        """ The number of spiders in a hypergraph diagram. """
        return self._n_spiders

    @property
    def wires(self):
        """ The wires of a hypergraph diagram. """
        return self._wires

    @property
    def spider_types(self):
        """ Mapping from spider to type. """
        return self._spider_types

    @property
    def ports(self):
        """ The ports of a hypergraph diagram. """
        return self._ports

    @property
    def is_hetero_monogamous(self):
        """
        Checks hetero-monogamy, i.e. whether self.wires induces a bijection::

            len(self.dom) + sum(len(box.dom) for box in boxes)
            == self.n_spiders - len(self._scalar_spiders)
            == sum(len(box.cod) for box in boxes) + len(self.dom)

        In that case, the diagram actually lives in a traced category.

        Examples
        --------

        >>> x, y = types(" x y")
        >>> f = Box('f', x, y)
        >>> assert f.is_hetero_monogamous
        >>> assert (f >> f[::-1]).is_hetero_monogamous

        >>> assert Spider(0, 0, x).is_hetero_monogamous

        >>> cycle = Cap(x, x) >> Id(x) @ (f >> f[::-1]) >> Cup(x, x)
        >>> assert cycle.is_hetero_monogamous

        >>> assert not f.transpose().is_hetero_monogamous
        >>> assert not Cup(x, x).is_hetero_monogamous
        >>> assert not Spider(1, 2, x).is_hetero_monogamous
        """
        inputs = self.wires[:len(self.dom)]
        outputs = self.wires[len(self.wires) - len(self.cod):]
        for dom_wires, cod_wires in self.box_wires:
            inputs += cod_wires
            outputs += dom_wires
        return sorted(inputs) == sorted(outputs)\
            == list(range(self.n_spiders - len(self._scalar_spiders)))

    @property
    def is_monogamous(self):
        """
        Checks monogamy, i.e. each spider is connected to two or zero ports.
        In that case, the diagram actually lives in a compact-closed category,
        i.e. it can be drawn using only swaps, cups and caps.

        Examples
        --------

        >>> x, y = types(" x y")
        >>> f = Box('f', x, y)
        >>> assert f.is_monogamous and f.transpose().is_monogamous
        >>> assert Cup(x, x).is_monogamous and Cap(x, x).is_monogamous
        >>> assert Spider(0, 0, x).is_monogamous
        >>> assert not Spider(1, 2, x).is_monogamous
        """
        return all(
            self.wires.count(i) in [0, 2] for i in range(self.n_spiders))

    @property
    def is_progressive(self):
        """
        Checks progressivity, i.e. wires are monotone w.r.t. box index.
        If the diagram is progressive, hetero-monogamous and it doesn't have
        any scalar spiders, then it actually lives in a symmetric monoidal
        category, i.e. it can be drawn using only swaps.

        Examples
        --------

        >>> x, y = types("x y")
        >>> f = Box('f', x, y)
        >>> assert f.is_progressive
        >>> assert (f >> f[::-1]).is_progressive

        >>> cycle = Cap(x, x) >> Id(x) @ (f >> f[::-1]) >> Cup(x, x)
        >>> assert not cycle.is_progressive
        """
        scan = set(self.wires[:len(self.dom)])
        for dom_wires, cod_wires in self.box_wires:
            if not set(dom_wires) <= scan:
                return False
            scan = scan.union(set(cod_wires))
        return True

    def to_nx(self):
        graph = Graph()
        graph.add_nodes_from(
            Node("spider", i=i) for i in range(self.n_spiders))
        graph.add_edges_from(
            (Node("input", i=i), Node("spider", i=j))
            for i, j in enumerate(self.wires[:len(self.dom)]))
        for i, (dom_wires, cod_wires) in enumerate(self.box_wires):
            graph.add_node(Node("box", i=i))
            graph.add_edges_from(
                (Node("box", i=i), Node("spider", i=j))
                for j in dom_wires + cod_wires)
        graph.add_edges_from(
            (Node("output", i=i), Node("spider", i=j))
            for i, j in enumerate(
                self.wires[len(self.wires) - len(self.cod):]))
        return graph

    def spring_layout(self, seed=None, k=None):
        if seed is not None:
            random.seed(seed)
        graph, pos = self.to_nx(), {}
        height = len(self.boxes) + self.n_spiders
        width = max(len(self.dom), len(self.cod))
        for i, _ in enumerate(self.dom):
            pos[Node("input", i=i)] = (i, height)
        for node in [Node("spider", i=i) for i in range(self.n_spiders)] + [
                Node("box", i=i) for i, _ in enumerate(self.boxes)]:
            pos[node] = (
                random.uniform(-width / 2, width / 2),
                random.uniform(0, height))
        for i, _ in enumerate(self.cod):
            pos[Node("output", i=i)] = (i, 0)
        fixed = [Node("input", i=i) for i, _ in enumerate(self.dom)] + [
            Node("output", i=i) for i, _ in enumerate(self.cod)]
        pos = spring_layout(graph, pos=pos, fixed=fixed, k=k, seed=seed)
        return graph, pos

    def draw(self, seed=None, k=None):
        graph, pos = self.spring_layout(seed=seed, k=k)
        for i, (dom_wires, cod_wires) in enumerate(self.box_wires):
            box_node = Node("box", i=i)
            for case, wires in [("dom", dom_wires), ("cod", cod_wires)]:
                for j, spider in enumerate(wires):
                    spider_node = Node("spider", i=spider)
                    port_node = Node(case, i=i, j=j)
                    graph.remove_edge(box_node, spider_node)
                    graph.add_edge(box_node, port_node)
                    graph.add_edge(port_node, spider_node)
                    x, y = pos[box_node]
                    y += .25 if case == "dom" else -.25
                    x -= .1 * (len(wires[:-1]) / 2 - j)
                    pos[port_node] = x, y
        labels = {
            node: self.spider_types[node.i] if node.kind == "spider"
            else self.boxes[node.i].name if node.kind == "box" else ""
            for node in graph.nodes}
        nodelist = list(graph.nodes)
        node_size = [
            300 if node.kind in ["spider", "box"] else 0 for node in nodelist]
        draw_networkx(
            graph, pos=pos, labels=labels,
            nodelist=nodelist, node_size=node_size,
            node_color="white", edgecolors="black")
        plt.show()

    @property
    def box_wires(self):
        """
        The wires connecting the boxes of a hypergraph diagram.

        Returns a list of length :code:`len(self.boxes)` such that::

            dom_wires, cod_wires = self.box_wires[i]
            len(dom_wires) == len(box.dom) and len(cod_wires) == len(box.cod)

        for :code:`box = self.boxes[i]`.
        """
        result, i = [], len(self.dom)
        for box in self.boxes:
            dom_wires = self.wires[i:i + len(box.dom)]
            cod_wires = self.wires[i + len(box.dom):i + len(box.dom @ box.cod)]
            result.append((dom_wires, cod_wires))
            i += len(box.dom @ box.cod)
        return result

    def then(self, other):
        """ Composition of two hypergraph diagrams, i.e. their pushout. """
        if not self.cod == other.dom:
            raise AxiomError
        dom, cod, boxes = self.dom, other.cod, self.boxes + other.boxes
        self_boundary = self.wires[len(self.wires) - len(self.cod):]
        other_boundary = other.wires[:len(other.dom)]
        graph = Graph([
            (("b", i), ("self", j)) for i, j in enumerate(self_boundary)
            ] + [
            (("b", i), ("other", j)) for i, j in enumerate(other_boundary)])
        components, self_pushout, other_pushout = set(), dict(), dict()
        for i, component in enumerate(connected_components(graph)):
            components.add(i)
            for case, j in component:
                if case == "self":
                    self_pushout[j] = i
                if case == "other":
                    other_pushout[j] = i
        self_spiders = set(range(self.n_spiders)) - set(self_boundary)
        self_pushout.update({
            j: len(components) + j
            for i, j in enumerate(self.wires) if j in self_spiders})
        other_spiders = set(range(other.n_spiders)) - set(other_boundary)
        other_pushout.update({
            j: len(components) + len(self_spiders) + j
            for i, j in enumerate(other.wires) if j in other_spiders})
        wires = [
            self_pushout[i] for i in self.wires[:
                len(self.wires) - len(self.cod)]]\
            + [other_pushout[i] for i in other.wires[len(other.dom):]]
        spider_types = {
            self_pushout[i]: t for i, t in enumerate(self.spider_types)}
        spider_types.update({
            other_pushout[i]: t for i, t in enumerate(other.spider_types)})
        return Diagram(dom, cod, boxes, wires, spider_types)

    def tensor(self, other):
        """ Tensor of two hypergraph diagrams, i.e. their disjoint union. """
        dom, cod = self.dom @ other.dom, self.cod @ other.cod
        boxes = self.boxes + other.boxes
        dom_wires = self.wires[:len(self.dom)] + [
            self.n_spiders + i for i in other.wires[:len(other.dom)]]
        box_wires = self.wires[len(self.dom):-len(self.cod) or len(self.wires)]
        box_wires += [self.n_spiders + i for i in other.wires[
            len(other.dom):-len(other.cod) or len(other.wires)]]
        cod_wires = self.wires[len(self.wires) - len(self.cod):] + [
            self.n_spiders + i
            for i in other.wires[len(other.wires) - len(other.cod):]]
        wires = dom_wires + box_wires + cod_wires
        spider_types = self.spider_types + other.spider_types
        return Diagram(dom, cod, boxes, wires, spider_types)

    __matmul__ = tensor

    def dagger(self):
        dom, cod = self.cod, self.cod
        dom_wires = self.wires[len(self.wires) - len(self.cod):]
        box_wires = sum([
            cod_wires + dom_wires
            for dom_wires, cod_wires in self.box_wires[::-1]], [])
        cod_wires = self.wires[:len(self.dom)]
        wires = dom_wires + box_wires + cod_wires
        return Diagram(dom, cod, boxes, wires, self.spider_types)

    def __getitem__(self, key):
        if key == slice(None, None, -1):
            return self.dagger()
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, Diagram):
            return False
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in ['dom', 'cod', 'boxes', 'wires', 'n_spiders'])

    def __repr__(self):
        data = list(map(repr, [self.dom, self.cod, self.boxes, self.wires]))
        data += [
            ", n_spiders={}".format(self.n_spiders)
            if self.scalar_spiders else ""]
        return "Diagram({}, {}, {}, {}{})".format(*data)

    transpose = rigid.Diagram.transpose


class Box(cat.Box, Diagram):
    """ Box in a :class:`discopy.hypergraph.Diagram`. """
    def __init__(self, name, dom, cod, **params):
        cat.Box.__init__(self, name, dom, cod, **params)
        boxes, spiders = [self], list(range(len(dom @ cod)))
        wires = 2 * list(range(len(dom)))\
            + 2 * list(range(len(dom), len(dom @ cod)))
        Diagram.__init__(self, dom, cod, boxes, wires)


class Id(Diagram):
    """ Identity diagram. """
    def __init__(self, dom):
        super().__init__(dom, dom, [], 2 * list(range(len(dom))))


class Swap(Diagram):
    """ Swap diagram. """
    def __init__(self, left, right):
        dom, cod = left @ right, right @ left
        boxes, wires = [], list(range(len(dom)))\
            + list(range(len(left), len(dom))) + list(range(len(left)))
        super().__init__(dom, cod, boxes, wires)


class Spider(Diagram):
    """ Spider diagram. """
    def __init__(self, n_legs_in, n_legs_out, typ):
        dom, cod = typ ** n_legs_in, typ ** n_legs_out
        boxes, spider_types = [], list(map(Ty, typ))
        wires = (n_legs_in + n_legs_out) * list(range(len(typ)))
        super().__init__(dom, cod, boxes, wires, spider_types)


class Cup(Diagram):
    """ Cup diagram. """
    def __init__(self, left, right):
        if not left.r == right:
            raise AxiomError
        wires = list(range(len(left))) + list(reversed(range(len(left))))
        super().__init__(left @ right, Ty(), [], wires)


class Cap(Diagram):
    """ Cap diagram. """
    def __init__(self, left, right):
        if not left.r == right:
            raise AxiomError
        wires = list(range(len(left))) + list(reversed(range(len(left))))
        super().__init__(Ty(), left @ right, [], wires)



Diagram.id = Id
Diagram.swap = Swap
Diagram.spiders = Spider
Diagram.cups, Diagram.caps = Cup, Cap