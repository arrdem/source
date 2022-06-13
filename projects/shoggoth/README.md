# Shoggot'im

> "The shoggot'im, they're called: servitors. There are several kinds of advanced robotic systems made out of molecular components: they can change shape, restructure material at the atomic level -- act like corrosive acid, or secrete diamonds. Some of them are like a tenuous mist -- what Doctor Drexler at MIT calls a utility fog -- while others are more like an oily globule. Apparently they may be able to manufacture more of themselves, but they're not really alive in any meaning of the term we're familiar with. They're programmable, like robots, using a command language deduced from recovered records of the forerunners who left them here. The Molotov Raid of 1930 brought back a large consignment of them; all we have to go on are the scraps they missed, and reports by the Antarctic Survey. Professor Liebkunst's files in particular are most frustrating --''
>
> ~ Charlie Stross, "A Colder War"

> The greatest performance improvement of all is when a system goes from not-working to working.
>
> ~ John Ousterhout

Shoggoth is a language designed to provide highly durable, portable processes.
Much like Eve, it's intended to be an experiment at enabling classes of programs and making some hard things easier.

Shoggoth runs atop a custom platform named Ichor, which aims to trivialize providing these properties and help the implementer focus by eliminating context.

## Ichor

The Ichor virtual machine is a toy.
The implementation presented here is merely as an experimental platform providing a "clean slate" target for compilation.
Ichor should be somewhat familiar to students of JVM bytecode, Fourth or UXN but has different priorities.

Ichor is perhaps best explained as a reaction to the JVM.
To be clear, the JVM is an incredible success story.
But it has some decisions baked in that can't be walked back, such as the existence of `Object.equals()` and the primacy of classes for structuring both data and code.

Ichor exists because it's much easier to define "snapshotting" the state of a flat loop bytecode interpreter with a stack than a recursive interpreter.
The objectives of building durable and portable processes/actors in Shoggoth requires the ability to take a snapshot of program state and persist it to a shared store for REMOTE or EVENTUAL resumption.
Think call/cc except with suspend or await happening across a network and database and scheduler boundary.

Like the JVM, Ichor is a high-level 'struct' or 'object' oriented VM.
Unlike the JVM which provides generics by using type erasure founded on casts and a shared bottom type (`Object`), Ichor has no `null` or ⊥ type.
Ichor has only user-defined closed variant types and structs without inheritance or methods.

Unlike the JVM, Ichor names "functions" and "types" including their generic parameters.
This allows for pervasive name overloading on both argument and return signature without the need for renaming or munging.

Unlike the JVM, Ichor does not make mutability readily available.
There is no concept of a mutable local value, or of a mutable variant or struct.
"Place oriented programming" can be achieved only through explicit use of a mutable reference type which cannot be defined by the user.
This is a bet that a platform founded on pervasive forwarding of immutability can prove viable.
It may not pan out.

Unlike most VMs, Ichor makes no effort to make user-defined C extensions easy.
They're likely to remain difficult-to-impossible as they conflict directly with other design priorities.

## Shoggoth

The Shoggoth language is an ML in Lisp's clothing.
While notationally a Lisp due entirely to the implementer's preference, Shoggoth has far more in common with an ML or other statically and generically typed language than with a unityped Lisp or interpreted language.

## License

While the source for this project happens to be published no grant of rights is made.
