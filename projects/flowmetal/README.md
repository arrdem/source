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

## Wait what?

Okay.
In simpler words, Flowmetal is an interpreted lisp which can use a datastore of your choice for durability.
Other systems can attach to Flowmetal's datastore and send events to and receive them from Flowmetal.
For instance Flowmetal contains a reference implementation of a HTTP callback connector and of a HTTP request connector.

A possible Flowmetal setup looks something like this -

```
                      +----------------------------+
                    +---------------------------+  |
                  +--------------------------+  |--+
                  | External HTTP service(s) |--+
                  +--------------------------+
                     ^                  ^
                     |                  |
                     v                  v
   +-----------------------+     +------------------------+
   | HTTP server connector |     | HTTP request connector |
   +-----------------------+     +------------------------+
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

In this setup, the Flowmetal interpreters are able to interact with an external HTTP service; sending and receiving webhooks with Flowmetal programs waiting for those external events to arrive.

For instance this program would use the external connector stubs to build up interaction(s) with an external system.

```lisp
 


```


Comparisons to Apache Airflow are at least in this setup pretty apt, although Flowmetal's durable execution model makes it much more suitable for providing reliable workflows and its DSL is more approachable.

## License

Mirrored from https://git.arrdem.com/arrdem/flowmetal

Published under the MIT license. See [LICENSE.md](LICENSE.md)
