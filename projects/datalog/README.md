# Datalog

An implementation of Datalog in Python.

## What is Datalog?

[Datalog](https://en.wikipedia.org/wiki/Datalog) is a fully declarative language for expressing relational data and queries, typically written using a syntactic subset of Prolog.
Its most interesting feature compared to other relational languages such as SQL is that it features production rules.

Briefly, a datalog database consists of rules and tuples.

Tuples are written `a(b, "c", 126, ...).`, require no declaration eg.
of table, may be of arbitrary even varying length.

Rules are written `f(A, B) :- a(A), b(B)` and when evaluated produce tuples.
This rule for instance would define `∀ aₑ∈a, bₑ∈b f(a, b)` eg the cross-product of the elements of the tuple sets `a(A)` and `b(B)`.

## Quickstart

We're gonna make use of the [datalog.easy](#datalog.easy) API.
It's somewhat simplified and definitely has sharp edges, but has much better ergonomics than working directly with the query engine from Python.

```
# Pull in the datalog.easy package
>>> from datalog import easy
# Read some tuples into a Dataset.
#
# Because the base Dataset class has some limitations, easy gives you
# an instance of the IndexedDataset which is best supported
>>> db = read('''
... edge(a, b).
... edge(b, c).
... edge(c, d).
... edge(d, e).
... ''')
```
Now that we've got a db instance, we can run some queries over it.

The two core operations are Select and Join.
Select selects tuples - both constants and from rules.
Join selects several tuples at once by unifying logic variables.

Let's select some tuples first.

Select returns a sequence of pairs `(tuples, bindings)`, where tuples are the selected tuples (always one tuple in fact), and bindings is a mapping of LVars to bound constants.

```
>>> easy.select(db, ('edge', 'a', 'b'))
[((('edge', 'a', 'b'),), {})]
```

Cool!
But what if we wanted to find all edges from a?
This is where logic variables come in.
Logic variables are written as capitalized words in textual datalog, and the easy package recognizes capitalized strings as logic variables when processing queries.

There's only one such tuple, `edge(a, b)`, but lets see if we find it.

```
>>> easy.select(db, ('edge', 'a', 'B'))
[((('edge', 'a', 'b'),), {'B': 'b'})] 
```

Nice.
But what of joins?
Rules are really a way to give a name to the result of a join, but we can do joins directly too.
For instance, we could try to select all contiguous 2-segment paths.

Unlike select which takes a single tuple, join takes a sequence of tuples to simultaneously satisfy.
However select like join returns a sequence of pairs `(tuples, bindings)`, where tuples may actually have many elements.

In this case, we're selecting pairs of adjacent edges, so we'll get two tuples and three bindings back in each result.

```
>>> easy.join(db, [
...   ('edge', 'A', 'B'),  # Any edge, ending at B
...   ('edge', 'B', 'C')   # Any edge, beginning at the same B
... ])
[((('edge', 'a', 'b'),
   ('edge', 'b', 'c')),
  {'A': 'a', 'B': 'b', 'C': 'c'}),
 ((('edge', 'b', 'c'),
   ('edge', 'c', 'd')),
  {'A': 'b', 'B': 'c', 'C': 'd'}),
 ((('edge', 'c', 'd'),
   ('edge', 'd', 'e')),
  {'A': 'c', 'B': 'd', 'C': 'e'})]
```

## API

### `datalog.types`
<span id="#datalog.types" />

The types package provides the core representation used by the rest of the system.
It defines the `Constant(value)` and `LVar(name)` tuples types.

A datalog tuple `a(b, c)` is internally represented as `(Constant('a'), Constant('b'), Constant('c')')`.
Tuples containing logic variables simply contain `LVar` instances in addition to `Constant` values.

The `LTuple` type alias is for tuples which contain both constants and logic variables.

The `CTuple` type alias is for tuples containing only constants.

A `Rule(pattern, clauses)` is a pair of an `LTuple` being the pattern for the tuples produced by the rule, and a sequence of clauses being `LTuple` values representing join constraints on the result of the rule.

The types package also defines the `Dataset` class.
A `Dataset` is a container for a sequence of tuples, and a sequence of rules which define tuples.
In fact the `Dataset` class only has three methods `rules()`, `tuples()` and `merge(other)`.

The query planners work mostly in terms of `Dataset` instances, although extensions of `Dataset` may be better supported.

`CachedDataset` is an extension of the `Dataset` type which allows the query engine to cache the result(s) of evaluating rules.
This enables recursive rule evaluation, and some other optimizations.

`IndexedDataset` is an extension of `CachedDataset` which also features support for indices which can reduce the amount of data processed.

### `datalog.parser`
<span id="#datalog.parser" />

This package contains only generated code, and is used to implement the reader.
Its contents are unstable.

### `datalog.reader`
<span id="#datalog.reader" />

The reader only intentionally exposes three methods - `read` aka `read_dataset` which accepts a string and an optional kwarg `db_cls` being a class extending `Dataset` into which tuples and rules should be read.

It also exposes `read_command` which returns a pair `(op: str, val: Either[Rule, LTuple])`.
This function is used to implement parts of the REPL, packaged separately ([PyPi](https://pypi.org/package/arrdem/datalog.shell), [git](https://git.arrdem.com/arrdem/datalog-shell)).

### `datalog.evaluator`
<span id="#datalog.evaluator" />

At present, the evaluator only contains two methods - `select` and `join`.
Select and join are mutually recursive, because rule evaluation is recursively selecting the results of joins.

At present, there is only one implementation of select and join in the system.
In the future, this interface will be replaced to add support for query planners.

Users should prefer the generally stable `datalog.easy` interface to working directly with the evaluator.

### `datalog.easy`
<span id="#datalog.easy" />

A shim over the reader and evaluator designed to make interacting with the evaluator from python more convenient.
Not simpler, just more convenient.

`read(str, db_cls=IndexedDataset)` is just a shim to `datalog.reader.read` with a better default class.

`select(db: Dataset, query: LTuple)` eagerly evaluates all results instead of producing a generator, eliminating `Constant()` and `LVar()` wrappers in both tuples and bindings.

`join(db: Dataset, query: Sequence[LTuple])` likewise eagerly evaluates all results, and likewise simplifies results.

## Usage

```
$ pip install --user arrdem.datalog
```

### Limitations

Recursion may have some completeness bugs. I have not yet encountered any, but I also don't have a strong proof of correctness for the recursive evaluation of rules yet.

The current implementation of negated clauses CANNOT propagate positive information. This means that negated clauses can only be used in conjunction with positive clauses. It's not clear if this is an essential limitation.

There is as of yet no query planner - not even segmenting rules and tuples by relation to restrict evaluation. This means that the complexity of a query is `O(dataset * term count)`, which is clearly less than ideal.

## License

Mirrored from https://git.arrdem.com/arrdem/datalog-py

Published under the MIT license. See [LICENSE.md](LICENSE.md)
