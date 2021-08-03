# Flowmetal

> A shining mercurial metal laden with sensors and almost infinitely reconfigurable.
>
> The stuff of which robots and servitors are made.

Flowmetal is a substrate for automation.
It attempts to provide a programming environment wherein programs are durable, evented and asynchronous aimed at what would traditionally be described as scripting or coordination.

Let's unpack these terms.

**Durable** - programs and their state are not dynamic and RAM located as with traditional models of processes.
Instead programs and their state are always persisted to storage.
This allows programs to sleep for a long time or even move seamlessly between machines.

**Evented** - durability is implemented in an event sourced style.
Each program retails - or at least has the opportunity to retain - both a log of any external events and of its own execution.
This allows for programs to easily rebuild their state, simplifies the durable programming model, and greatly simplifies debugging as intermediary states are retained and inspectable.

This also allows for external systems such as REST callback APIs, databases and such to easily integrate with Flowmetal programs as event sources.
It also allows bidirectional communication between Flowmetal programs and other more traditional programming environments.
Anything that can communicate with Flowmetal can provide function implementations, or call Flowmetal programs!

**Asynchronous** - thanks to Flowmetal's evented execution model, waiting for slow external events either synchronously or asynchronously is second nature!
Flowmetal is especially good at waiting for very, very slow external operations.
Stuff like webhooks and batch processes.

**Scripting** - the tradeoff Flowmetal makes for the evented model is that it's slow.
While Flowmetal foreign functions could be fast, Flowmetal's interpreter isn't designed for speed.
It's designed for eventing and ensuring durability.
This makes Flowmetal suitable for interacting with and coordinating other systems, but it's not gonna win any benchmark games.

## An overview

In the systems world we have SH, Borne SH, BASH, ZSH and friends which provide a common interface for connecting processes together.
However in the distributed system world we don't have a good parallel for connecting microservices; especially where complex failure handling is required.

I previously [blogged a bit](https://www.arrdem.com/2019/04/01/the_silver_tower/) about some ideas for what this could look like.
I'm convinced that a programming environment based around [virtual resiliency](https://www.microsoft.com/en-us/research/publication/a-m-b-r-o-s-i-a-providing-performant-virtual-resiliency-for-distributed-applications/) is a worthwhile goal (having independently invented it) and worth trying to bring to a mainstream general purpose platform like Python.

Flowmetal is an interpreted language backed by a durable event store.
The execution history of a program persists to the durable store as execution precedes.
If an interpretation step fails to persist, it can't have external effects.
This is the fundamental insight behind Microsoft AMBROSIA.
The event store also provides Flowmetal's only interface for communicating with external systems.
Other systems can attach to Flowmetal's data store and send events to and receive them from Flowmetal.
For instance Flowmetal contains a reference implementation of a HTTP callback connector and of a HTTP request connector.
This allows Flowmetal programs to request that HTTP requests be sent on their behalf, consume the result, and wait for callbacks.

A Flowmetal setup could look something like this -

```
                 +----------------------------+
               +---------------------------+  |
             +--------------------------+  |--+
             | External HTTP service(s) |--+
             +--------------------------+
                ^                  ^
                |                  |
                v                  v
+-----------------------+   +------------------------+
| HTTP server connector |   | HTTP request connector |
+-----------------------+   +------------------------+
                ^                  ^
                |                  |
                v                  v
               +--------------------+
               | Shared event store |
               +--------------------+
                          ^
                          |
                          v
            +--------------------------+
            | Flowmetal interpreter(s) |
            +--------------------------+
```

## License

Mirrored from https://git.arrdem.com/arrdem/flowmetal

Published under the MIT license. See [LICENSE.md](LICENSE.md)
