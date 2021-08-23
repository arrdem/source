# Lilith

> The theme of the jam is "first-class comments".

Okay so _enormous bong rip_ what is a comment anyway.

### Comments

```c
// foo bar baz
```

``` clojure
; text that the parser throws away

(def <name> <value>)
(def ^{:doc "foo bar baz"} <name> <value>)
```

Traditionally, comments are just text that the language throws away or that the compiler ignores.
For instance `//` or `;` comments just discard an entire line.
`/* ... */` or `(* ... *)` comments discard a block.

Languages that want to play games with comment inspection need customized parsers different from the one used by the language itself to extract this text which implementers usually just drop on the floor.

### Docstrings

Another take on the idea of putting text in the source file but privileging it more is docstrings - special strings understood by the language to have interpretation.

``` python
"""modules have __doc__ as a property defined by the FIRST heredoc-string in the file"""

def foo(a, b):
    """Adds a and b.

    >>> foo(1, 2)
    3
    """

    return a + b

```

``` clojure
(defn foo [a b]
    "Adds a and b

    >>> (foo 1 2)
    => 3
    "
    (+ a b))
```

As we're thinking about "comments" and "documentation", docstrings are a lot better than reader discard comments because we can at least do something with them.
But they're still very much second class in that they presuppose "documentation" for an artifact or a program is limited to API docs.

To the extent docstrings are overloaded for other DSLs like doctests, those DSLs are extremely second if not third class.
There's no syntax support for them in the language, a separate parser must be used, editors don't understand when you embed code or other languages in strings ... the entire experience is just limited.

### Literate Programming (tangle/weave)

Old-school Knuth [literate programming](https://en.wikipedia.org/wiki/Literate_programming) is AN answer for how to center documentation over the program.
In the LP world, your program isn't so much a program as it is a book containing code blocks that can be "woven" together into a program a compiler can eat.
From a literature perspective, this is a great idea.
Programs are absolutely literature, and being able to produce a fully fledged and formatted book out of a "program" rather than just an API listing out of a "program" is great.

Unfortunately tangle/weave systems don't align well with language boundaries.
They deliberately leap over them, and in doing so disable language tooling.
So what if we could build a language that natively has something like tangle/weave?
Make comments or perhaps more accurately document DSLs "first-class" and values that can reference terms from the language, and in turn be referenced by the language.

## Enter Lilith

Lilith is a sketch at what if you took the ideas from literate programming (having fragments of text from which programs are composed) but deliberately DID NOT privilege the "source" for a "document" over the "source" for the "program".
Documents, DSLs and programs could be co-equal and co-resident artifacts.
Users could define their own (textual) macros, DSLs with evaluation order and weaving of fragments together into multiple documents or indices.

To achieve this vision, Lilith uses a context sensitive block-prefixed syntax which SHOULD be uncommon enough not to involve collisions with other languages.

Lilith is an [M-expression](https://en.wikipedia.org/wiki/M-expression) esque language with a "meta" language and two "object" languages.

The meta-language is `!` prefixed M-expressions.
At present the meta-language has two directives, `!def[<name>, <language>]` and `!import[<from>, ...]`.

Lilith interpretation is actually dual (or potentially N) interpreter based.
When a given name is evaluated, its body or definition is evaluated in the given language.
This Lilith implementation is bootstrapped off of Python, and provides two built-in languages, `lil` AKA Lilith and `py` AKA python3.
For instance, this snippet would define a pair of Lilith "foreign" functions in Python (`gt` and `sub`), which would then be used from the definition of `fib`.

``` lilith
!def[gt, py]
return lambda x, y: x > y

!def[sub, py]
return lambda x, y: x - y

!def[fib_tests, doctest]
fib[1] = 1
fib[2] = 1
fib[3] = 2

!def[fib, lil]
lambda[[x]
       , cond[[gt[x, 1],
                add[fib[sub[x, 1]], fib[sub[x, 2]]]],
              [true,
                0]]]
]
```

Where this gets really fun is that there are no restrictions on the number of sub-languages which Lilith can support.
For instance, Markdown could be a sub-language.

``` lilith
!def[docstring, md]
This module has a docstring, defined to be whatever the `md` language processor produces.
For instance, this could be compiled HTML.
Or it could be source markdown, post-validation.

When executed, this module will evaluate the docstring and print it.

!def[main, lil]
print[docstring]
```

We could even get real weird with it, embedding GraphViz graphs or YAML documents within a Lilith file and composing them all together.

### The Demo

``` shell
$ python3 setup.py develop
$ lil
>>> print["hello, world!"]
hello, world!
```

### Generating HTML with Markdown from the designdoc

``` shell
$ lil src/lark/designdoc.lil
<h1>The Lilith Pitch</h1>
<p>Code is more than .. just code for the compiler.
....
```

### Presentation videos

- [short walkthrough](https://twitter.com/arrdem/status/1429486908833292295)
- [long walkthrough](https://twitter.com/arrdem/status/1429486908833292295)

## Limitations and broken windows

While this Lilith prototype succeeds in making document terms usable from the "host" language (Lilith), it doesn't currently support going the other way.
A more complete Lilith would probably feature a way to embed Lilith evaluation within non-Lilith languages (ab)using read-time eval and treating document bodies like Python f-strings.
An even more context sensitive parser would be needed to implement this, but that's eminently doable.

The Lilith language itself is a PITA to write.
While `!def[]` is a nice hack, `!def[] lambda` is ... kinda silly.
Especially because there's no way to attach a docstring to a def.
Perhaps a convention `!def[foo, ...]`, `!def[foo.__doc__, ...]` could hack around that, allowing docstrings to be defined separately but it's not thought out.

The Lilith language itself is wildly incomplete.
Being able to piggy-back off of the host Python interpreter has been good for a lot, but ultimately the language is missing a lot of basic lisp-isms:
- `eval[]` (all the machinery is here to do this)
- `apply[]` (although this is trivial to implement)
- `or[]`
- `not[]`
- `=[]`
- `let[]`
- `if[]`

The module/namespace/def system is Clojure derived and worked out pretty well, but `!import` can't trigger code loading as presently factored.

## License

This code is copyright Reid D. 'arrdem' McKenzie 2021, published under the terms of the MIT license.
