# Datalog.Shell

A shell for my Datalog engine.

## What is Datalog?

[Datalog](https://en.wikipedia.org/wiki/Datalog) is a fully
declarative language for expressing relational data and queries,
typically written using a syntactic subset of Prolog. Its most
interesting feature compared to other relational languages such as SQL
is that it features production rules.

Briefly, a datalog database consists of rules and tuples. Tuples are
written `a(b, "c", 126, ...).`, require no declaration eg. of table,
may be of arbitrary even varying length. The elements of this tuple
are strings which may be written as bare words or quoted.

In the interpreter (or a file), we could define a small graph as such -

```
$ datalog
>>> edge(a, b).
⇒ edge('a', 'b')
>>> edge(b, c).
⇒ edge('b', 'c')
>>> edge(c, d).
⇒ edge('c', 'd')
```

But how can we query this? We can issue queries by entering a tuple
terminated with `?` instead of `.`.

For instance we could query if some tuples exist in the database -

```
>>> edge(a, b)?
⇒ edge('a', 'b')
>>> edge(d, f)?
⇒ Ø
>>> 
```

We did define `edge(a, b).` so our query returns that tuple. However
the tuple `edge(d, f).` was not defined, so our query produces no
results. Rather than printing nothing, the `Ø` symbol which denotes
the empty set is printed for clarity.

This is correct, but uninteresting. How can we find say all the edges
from `a`? We don't have a construct like wildcards with which to match
anything - yet.

Enter logic variables. Logic variables are capitalized words, `X`,
`Foo` and the like, which are interpreted as wildcards by the query
engine. Capitalized words are always understood as logic variables.

```
>>> edge(a, X)?
⇒ edge('a', 'b')
```

However unlike wildcards which simply match anything, logic variables
are unified within a query. Were we to write `edge(X, X)?` we would be
asking for the set of tuples such that both elements of the `edge`
tuple equate.

```
>>> edge(X, X)?
⇒ Ø
```

Of which we have none.

But what if we wanted to find paths between edges? Say to check if a
path existed from `a` to `d`. We'd need to find a way to unify many
logic variables together - and so far we've only seen queries of a
single tuple.

Enter rules. We can define productions by which the Datalog engine can
produce new tuples. Rules are written as a tuple "pattern" which may
contain constants or logic variables, followed by a sequence of
"clauses" separated by the `:-` assignment operator.

Rules are perhaps best understood as subqueries. A rule defines an
indefinite set of tuples such that over that set, the query clauses
are simultaneously satisfied. This is how we achieve complex queries.

There is no alternation - or - operator within a rule's body. However,
rules can share the same tuple "pattern".

So if we wanted to say find paths between edges in our database, we
could do so using two rules. One which defines a "simple" path, and
one which defines a path from `X` to `Y` recursively by querying for
an edge from `X` to an unconstrained `Z`, and then unifying that with
`path(Z, Y)`.

```
>>> path(X, Y) :- edge(X, Y).
⇒ path('X', 'Y') :- edge('X', 'Y').
>>> path(X, Y) :- edge(X, Z), path(Z, Y).
⇒ path('X', 'Y') :- edge('X', 'Z'), path('Z', 'Y').
>>> path(a, X)?
⇒ path('a', 'b')
⇒ path('a', 'c')
⇒ path('a', 'd')
```

We could also ask for all paths -

```
>>> path(X, Y)?
⇒ path('b', 'c')
⇒ path('a', 'b')
⇒ path('c', 'd')
⇒ path('b', 'd')
⇒ path('a', 'c')
⇒ path('a', 'd')
```

Datalog also supports negation. Within a rule, a tuple prefixed with
`~` becomes a negative statement. This allows us to express "does not
exist" relations, or antjoins. Note that this is only possible by
making the [closed world assumption](https://en.wikipedia.org/wiki/Closed-world_assumption).

Datalog also supports binary equality as a special relation. `=(X,Y)?`
is a nonsense query alone because the space of `X` and `Y` are
undefined. However within a rule body, equality (and negated
equality statements!) can be quite useful.

For convenience, the Datalog interpreter supports "retracting"
(deletion) of tuples and rules. `edge(a, b)!` would retract that
constant tuple, but we cannot retract `path(a, b)!` as that tuple is
generated by a rule. We can however retract the rule - `edge(X, Y)!`
which would remove both edge production rules from the database.

The Datalog interpreter also supports reading tuples (and rules) from
one or more files, each specified by the `--db <filename>` command
line argument.

## Usage

`pip install --user arrdem.datalog.shell`

This will install the `datalog` interpreter into your user-local
python `bin` directory, and pull down the core `arrdem.datalog` engine
as well.

## Status

This is a complete to my knowledge implementation of a traditional datalog.

Support is included for binary `=` as builtin relation, and for negated terms in
rules (prefixed with `~`)

Rules, and the recursive evaluation of rules is supported with some guards to
prevent infinite recursion.

The interactive interpreter supports definitions (terms ending in `.`),
retractions (terms ending in `!`) and queries (terms ending in `?`), see the
interpreter's `help` response for more details.

### Limitations

Recursion may have some completeness bugs. I have not yet encountered any, but I
also don't have a strong proof of correctness for the recursive evaluation of
rules yet.

The current implementation of negated clauses CANNOT propagate positive
information. This means that negated clauses can only be used in conjunction
with positive clauses. It's not clear if this is an essential limitation.

There is as of yet no query planner - not even segmenting rules and tuples by
relation to restrict evaluation. This means that the complexity of a query is
`O(dataset * term count)`, which is clearly less than ideal.

## License

Mirrored from https://git.arrdem.com/arrdem/datalog-py

Published under the MIT license. See [LICENSE.md](LICENSE.md)