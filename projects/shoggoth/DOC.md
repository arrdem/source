# "Documentation"

## Ichor ISA

### TRUE
```() -> (bool)```

Push the constant TRUE onto the stack.

### FALSE
```() -> (bool)```

Push the constant FALSE onto the stack.

### IF <target>
```(bool) -> ()```

Branch to another point if the top item of the stack is TRUE. Otherwise fall through.

Note that not, and, or, xor etc. can all be user or prelude defined functions given if.

### GOTO <target>
```() -> ()```

Branch to another point within the same bytecode segment. The target MUST be within the same module range as the
current function. Branching does NOT update the name or module of the current function.

### DUP <n>
```(A, B, ...) -> (A, B, A, B, ...)```

Duplicate the top N items of the stack.

### ROT <n>
```(A, B, ..., Z) -> (Z, A, B, ...)```

Rotate the top N elements of the stack by 1.

FIXME: What if you want to rotate by more than 1?

### DROP <n>
```(...: n, ...) -> (...)```

Drop the top N items of the stack.

### SLOT <n>
```(..., A) -> (A, ..., A)```

Copy the Nth (counting up from 0 at the bottom of the stack) item to the top of the stack.
Intended to allow users to emulate (immutable) frame locals for reused values.

### IDENTIFIERC <val>
```() -> (IDENTIFIER)```

An inline constant which produces an identifier to the stack.

Identifiers name functions, fields and types but are not strings.
They are a VM-internal naming structure with reference to the module.

#### Function identifiers

Function identifiers are written `<typevars>;<name>;<arglist>;<retlist>`.

For example the signature of `not` is `;not;bool;bool`.
Note that this name scheme allows for `;or;bool,bool;bool` and `;or;bool,bool,bool;bool` to co-exist simultaneously, and for overloading of names with type variables.

One could also have written `or` as `T;or;<funref T;bool>,T,T;T` if one were able to provide a truly generic test

This design is a deliberate reaction to the JVM which does not permit such name-overloading and is intended to enable semi-naive compilation of complex generic operations without munging or erasure.

#### Type identifiers

Type identifiers are written `<typevars>;<name>;<variantlist>`

For example the signature of `bool` is `;bool;<true>,<false>`

As with functions, this allows for generic overloading of names.
For example one could define `tuple` as `;tuple;<tuple>`, `A;tuple;<tuple A>`, `A,B;tuple;<tuple A,B>`, and soforth simultaneously.

### FUNREF
```(IDENTIFIER) -> (<FUNREF ... A; ... B>)```

Note that `;` ends a list here the arguments list and should be read as `to`.

Construct a reference to a static codepoint.

### CALLF <nargs>
```(<FUNREF ... A; ... B>, ... A) -> (... B)```

Call [funref]

Make a dynamic call to the function reference at the top of stack.
The callee will see a stack containg only the provided `nargs`.
A subsequent RETURN will return execution to the next point.

Executing a `CALL` pushes the name and module path of the current function.

### RETURN <nargs>
```(...) -> ()```

Return to the source of the last `CALL`. The returnee will see the top `nargs` values of the present stack
appended to theirs. All other values on the stack will be discarded.

Executing a `RETURN` pops (restores) the name and module path of the current function back to that of the caller.

If the call stack is empty, `RETURN` will exit the interpreter.


### CLOSUREF <nargs>
```(FUNREF<A, ... B; ... C>, A) -> (CLOSURE<... B; ... C>)```

Construct a closure over the function reference at the top of the stack. This may produce nullary closures.

### CLOSUREC <nargs>
```(CLOSURE<A, ... B; ... C>, A) -> (CLOSURE<... B; ... C>)```

Further close over the closure at the top of the stack. This may produce nullary closures.

### CALLC <nargs>
```(CLOSURE<... A; .. B>, ... A) -> (... B)```

Call [closure]

Make a dynamic call to the closure at the top of stack.
The callee will see a stack containg only the provided `nargs` and closed-overs.
A subsequent RETURN will return execution to the next point.

Executing a `CALL` pushes the name and module path of the current function.

### TYPEREF
```(IDENTIFIER) -> (TYPEREF)```

Produces a TYPEREF to the type named by the provided IDENTIFIER.

### FIELDREF
```(IDENTIFIER, TYPEREF) -> (FIELDREF)```


Produces a FIELDREF to the field named by the provided IDENTIFIER.
The FIELDREF must be within and with reference to a sum type.

### VARIANTREF
```(IDENTIFIER, TYPEREF) -> (VARIANTREF)```

Produce a VARIANTREF to an 'arm' of the given variant type.

### STRUCT <nargs>
```(STRUCTREF<S>, ...) -> (S)```

Consume the top N items of the stack, producing a struct of the type `structref`.

The name and module path of the current function MUST match the name and module path of `structref`.
The arity of this opcode MUST match the arity of the struct.
The signature of the struct MUST match the signature fo the top N of the stack.

### FLOAD
```(FIELDREF<f ⊢ T ∈ S>, S) -> (T)```
Consume the struct reference at the top of the stack, producing the value of the referenced field.

### FSTORE
```(FIELDREF<f ⊢ T ∈ S>, S, T) -> (S)```

Consume the struct reference at the top of the stack and a value, producing a new copy of the struct in which
that field has been updated to the new value.

### VARIANT <nargs>
```(VARIANTREF<a ⊢ A ⊂ B>, ...) -> (B)```

Construct an instance of an 'arm' of a variant.
The type of the 'arm' is considered to be the type of the whole variant.

The name and module path of the current function MUST match the name and module path of `VARIANTREF`.
The arity of this opcode MUST match the arity of the arm.
The signature of the arm MUST match the signature fo the top N of the stack.

### VTEST
```(VARIANTREF<a ⊢ A ⊂ B>, B) -> (bool)```

Test whether B is a given arm of a variant A .

### VLOAD
```(VARIANTREF<a ⊢ A ⊂ B>, B) -> (A)```

Load the value of the variant arm.
VLOAD errors (undefined) if B is not within the variant.
VLOAD errors (undefined) if the value in B is not an A - use VTEST as needed.

### ARRAY <nargs>
```(TYPEREF<Y>, ... ∈ Y) -> (ARRAY<Y>)```

Consume the top N items of the stack, producing an array of the type `typeref`.

### ALOAD
```(ARRAY<T>, NAT) -> (T)```

Consume a reference to an array and an index, producing the value at that index.

FIXME: Or a signal/fault.

### ASTORE
```(ARRAY<T>, NAT, T) -> (ARRAY<T>)```

Consume a value T, storing it at an index in the given array.
Produces the updated array as the top of stack.

### BREAK
Abort the interpreter

## Appendix

https://wiki.laptop.org/go/Forth_stack_operators
https://www.forth.com/starting-forth/2-stack-manipulation-operators-arithmetic/
https://docs.oracle.com/javase/specs/jvms/se18/html/jvms-6.html#jvms-6.5.swap
