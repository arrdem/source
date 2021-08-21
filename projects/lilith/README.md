# Lilith

> The theme of the jam is "first-class comments".

```c
// foo bar baz
```

``` clojure
; text that the parser throws away

(def <name> <value>)
(def ^{:doc "foo bar baz"} <name> <value>)
```

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

- Object code
- .... Other media?

``` clojure
(defn foo [a b]
    (!doc "")
    (!doctest "")
    (!test "")

    (!impl
       (+ a b)))
```

``` clojure
(defn foo [a b]
    "---
    doc: |
       Adds a and b

    ---
    doctest:
      - in: (foo 1 2)
        out: 3
    "
    )
```

``` org
#+TITLE: foo
* my bullet
  #+BEGIN_SRC clojure
    (defn foo [a b] (+ a b))
  #+END_SRC
```

`org-babel` `org-babel-tagle`

``` clojure
(defn foo [] ..)
```

####################################################################################################
