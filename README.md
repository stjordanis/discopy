# Distributional Compositional Python

`discopy` computes natural language meaning in pictures.

!["Alice loves Bob" in picture](figures/alice-loves-bob.png)

The recipe goes in three steps:

1) draw the picture

```python
from discopy.grammar import Pregroup, Word, Cup, Wire

s, n = Pregroup('s'), Pregroup('n')
Alice = Word('Alice', n)
loves = Word('loves', n.r + s + n.l)
Bob = Word('Bob', n)

grammar = Cup(n) @ Wire(s) @ Cup(n.l)
sentence = grammar << Alice @ loves @ Bob
```

2) define a model

```python
from discopy.grammar import Model

ob = {s: 1, n: 2}
ar = {Alice: [1, 0], loves: [0, 1, 1, 0], Bob: [0, 1]}
F = Model(ob, ar)
```

3) compute the meaning!

```python
assert F(sentence) == True
```

## Requirements

* `numpy` (>=1.17.2)

## Getting started

```shell
git clone https://github.com/toumix/discopy.git
python -m doctest discopy/*.py -v
```

## General Abstract Nonsense

`discopy` is a Python implementation of the categorical compositional distributional (DisCoCat) models, see [arXiv:1003.4394](https://arxiv.org/abs/1003.4394), [arXiv:1106.4058](https://arxiv.org/abs/1106.4058) [arXiv:1904.03478](https://arxiv.org/abs/1904.03478).

* `cat.Arrow`, `cat.Generator` implement free (dagger) categories.
* `cat.Functor` implements Python-valued functors.
* `moncat.Diagram`, `moncat.Box` implement free (dagger) monoidal categories.
* `moncat.MonoidalFunctor` implements free (dagger) monoidal functors.
* `matrix.NumpyFunctor` implements matrix-valued (dagger) monoidal functors.
* `disco.Pregroup`, `disco.Cup` and `disco.Cap` implement free dagger pivotal monoidal categories.
* `disco.Word`, `disco.Grammar`, `disco.Parse` implement pregroup grammars.
* `disco.Model` implements rigid monoidal functors and dagger pivotal monoidal functors.
