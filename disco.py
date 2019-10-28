import numpy as np
from diagram import Diagram, Box, Wire, MonoidalFunctor


class NumpyFunctor(MonoidalFunctor):
    def __call__(self, d):
        if not isinstance(d, Diagram):  # d must be an object
            return super().__call__(d)

        if isinstance(d, Box):
            return self.ar[d].reshape(self(d.dom) + self(d.cod))

        arr = 1
        for x in d.dom:
            arr = np.tensordot(arr, np.identity(self(x)), 0)
        arr = np.moveaxis(arr, [2 * i for i in range(len(d.dom))],
                               [i for i in range(len(d.dom))])  # bureaucracy!

        for f, n in zip(d.nodes, d.offsets):
            source = range(len(d.dom) + n, len(d.dom) + n + len(f.dom))
            target = range(len(f.dom))
            arr = np.tensordot(arr, self(f), (source, target))

            source = range(len(arr.shape) - len(f.cod), len(arr.shape))
            destination = range(len(d.dom) + n, len(d.dom) + n +len(f.cod))
            arr = np.moveaxis(arr, source, destination)  # more bureaucracy!

        return arr

x, y, z, w = 'x', 'y', 'z', 'w'
f, g, h = Box('f', [x], [x, y]), Box('g', [y, z], [w]), Box('h', [x, w], [x])
d = f.tensor(Wire(z)).then(Wire(x).tensor(g))

F0 = NumpyFunctor({x: 1, y: 2, z: 3, w: 4}, None)
F = NumpyFunctor(F0.ob, {a: np.zeros(F0(a.dom) + F0(a.cod)) for a in [f, g, h]})

assert F(d).shape == tuple(F(d.dom) + F(d.cod))
assert np.all(F(d.then(h)) == np.tensordot(F(d), F(h), 2))


class Type(list):
    def __init__(self, t, basic=False):
        if isinstance(t, str):
            self.basic = True
            super().__init__([(t, 0)])
        else:
            assert all(isinstance(b, str) and isinstance(z, int) for b, z in t)
            super().__init__(t)

    def __add__(self, other):
        return Type(list(self) + list(other))

    def __repr__(self):
        if self == []:
            return '[]'
        f = lambda z: - z * '.l' if z < 0 else z * '.r'
        return ' + '.join(b + f(z) for b, z in self)

    def __hash__(self):
        return hash(repr(self))

    @property
    def l(self):
        return Type([(b, z - 1) for b, z in self[::-1]])

    @property
    def r(self):
        return Type([(b, z + 1) for b, z in self[::-1]])

class RDiagram(Diagram):
    def __init__(self, dom, cod, nodes, offsets):
        assert all(isinstance(x, Type) for x in [dom, cod])
        super().__init__(dom, cod, nodes, offsets)

    def tensor(self, other):
        r = super().tensor(other)
        r.dom, r.cod = Type(r.dom), Type(r.cod)
        return r

class Word(RDiagram, Box):
    def __init__(self, w, t):
        assert isinstance(w, str)
        assert isinstance(t, Type)
        Box.__init__(self, (w, t), [(w, t)], t)

    def __repr__(self):
        return "Word" + str(self.name)

class Cup(RDiagram, Box):
    def __init__(self, x):
        Box.__init__(self, 'cup_{}'.format(x), x + x.r, [])

class Parse(Diagram):
    def __init__(self, words, cups):
        dom = [w.name for w in words]
        nodes = words[::-1]  # words are backwards to make offsets easier
        offsets = [len(words) - i - 1 for i in range(len(words))] + cups
        cod = Type([(b, z) for w in words for b, z in w.cod])
        for i in cups:
            x, y = cod[i], cod[i + 1]
            assert x[0] == y[0] and y[1] - x[1] == 1  # x and y are adjoints
            nodes.append(Cup(Type([x])))
            cod = Type(cod[:i] + cod[i + 2:])
        super().__init__(dom, cod, nodes, offsets)

class Model(NumpyFunctor):
    def __init__(self, ob, ar):
        assert all(x.basic for x in ob.keys())
        self.ob, self.ar = {x[0][0]: ob[x] for x in ob.keys()}, ar

    def __call__(self, d):
        if not isinstance(d, Diagram):
            # d must be an object: either a list, a basic type or a word
            if isinstance(d, list):
                return [self(x) for x in d]
            elif isinstance(d[0], str) and isinstance(d[1], int):
                return self.ob[d[0]]
            return 1

        if isinstance(d, Cup):
            return np.identity(self(d.dom[0]))

        return super().__call__(d)


s, n = Type('s'), Type('n')

alice, bob = Word('Alice', n), Word('Bob', n)
loves = Word('loves', n.r + s + n.l)
sentence = Parse([alice, loves, bob], [0, 1])

F = Model({s: 1, n: 2},
          {alice : np.array([1, 0]),
           bob : np.array([0, 1]),
           loves : np.array([0, 1, 1, 0])})

assert F(sentence) == True