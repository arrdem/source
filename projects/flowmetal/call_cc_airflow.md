# An Asynchronous, Distributed Task Engine

This document presents a design without reference implementation for a distributed programming system;
sometimes called a workflow engine.
It is intended to provide architectural level clarity allowing for the development of alternative designs or implementations as may suit.

## Problem Statement

In building, operating and maintaining distributed systems (many computers in concert) engineers face a tooling gap.

Within the confines of a single computer, we have shells (`bash`, `csh`, `zsh`, `oil` etc.)
and a suite of small programs which mesh together well enough for the completion of small tasks with ad-hoc automation.
This is an enormous tooling win, as it allows small tasks to be automated at least for a time with a minimum of effort and with tools close to hand.

In interacting with networks, communicating between computers is difficult with traditional tools and communication failure becomes an ever-present concern.
Traditional automation tools such as shells are inadequate for this environment because achieving network communication is excessively difficult.

In a distributed environment it cannot be assumed that a single machine can remain available to execute automation;
This requires an approach to automation which allows for the incremental execution of single tasks at a time with provisions for relocation and recovery should failure occur.

It also cannot be assumed that a single machine is sufficiently available to receive and process incoming events such as callbacks.
A distributed system is needed to wrangle distributed systems.

## Design Considerations

- Timeouts are everywhere
- Sub-Turing/boundable
- 

## Architectural Overview

### Events
Things that will happen, or time out.

### Actions
Things the workflow will do, or time out.

### Bindings
Data the workflow either was given or computed.

### Conditionals
Decisions the workflow may make.

### Functions
A convenient way to talk about fragments of control flow graph.

### Tracing & Reporting
