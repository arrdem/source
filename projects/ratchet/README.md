# Ratchet

> A process that is perceived to be changing steadily in a series of irreversible steps.
>
> The unstoppable march of history; if not progress.

Ratchet is a durable signaling mechanism.

Ratchet provides tools for implementing _durable_ messaging, event and request/response patterns useful for implementing reliable multiprocess or distributed architectures.

By _durable_, we mean that an acceptably performant commit log is used to record all signals and any changes to their states.

The decision to adopt an architectural commit log such as that implemented in Ratchet enables the components of a system to be more failure oblivious and pushes the overall system towards monotone or ratcheted behavior. If state was committed prior to a failure, it can easily be recovered. If state was not committed, well nothing happened.
