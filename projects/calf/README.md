# Calf

> Calf: Noun.
A young cow or ox.

Before I walked from the Clojure space, I kept throwing around the idea of "ox", an ur-clojure.
Ox was supposed to experiment with some stuff around immutable namespaces and code as data which never came to fruition.
I found the JVM environment burdensome, difficult to maintain velocity in, and my own ideas too un-formed to fit well into a rigorous object model.

Calf is a testbed.
It's supposed to be a lightweight, unstable, easy for me to hack on substrate for exploring those old ideas and some new ones.

Particularly I'm interested in:
- compilers-as-databases (or using databases)
- stream processing and process models of computation more akin to Erlang
- reliability sensitive programming models (failure, recovery, process supervision)

I previously [blogged a bit](https://www.arrdem.com/2019/04/01/the_silver_tower/) about some ideas for what this could look like.
I'm convinced that a programming environment based around [virtual resiliency](https://www.microsoft.com/en-us/research/publication/a-m-b-r-o-s-i-a-providing-performant-virtual-resiliency-for-distributed-applications/) is a worthwhile goal (having independently invented it) and worth trying to bring to a mainstream general purpose platform like Python.

## Manifesto

In the last decade, immutability has been affirmed in the programming mainstream as an effective tool for making programs and state more manageable, and one which has been repeatedly implemented at acceptable performance costs.
Especially in messaging based rather than state sharing environments, immutability and "data" oriented programming is becoming more and more common.

It also seems that much of the industry is moving towards message based reactive or network based connective systems.
Microservices seem to have won, and functions-as-a-service seem to be a rising trend reflecting a desire to offload or avoid deployment management rather than wrangle stateful services.

In these environments, programs begin to consist entirely of messaging with other programs over shared channels such as traditional HTTP or other RPC tools or message buses such as Kafka, gRPC, ThriftMux and soforth.

Key challenges with these connective services are:
- How they handle failure
- How they achieve reliability
- The ergonomic difficulties of building and deploying connective programs
- The operational difficulties of managing N-many 'reliable' services

Tools like Argo, Airflow and the like begin to talk about such networked or evented programs as DAGs; providing schedulers for sequencing actions and executors for performing actions.

Airflow provides a programmable Python scheduler environment, but fails to provide an execution isolation boundary (such as a container or other subprocess/`fork()` boundary) allowing users to bring their own dependencies.
Instead Airflow users must build custom Airflow packagings which bundle dependencies into the Airflow instance.
This means that Airflow deployments can only be centralized with difficulty due to shared dependencies and disparate dependency lifecycles and limits the return on investment of the platform by increasing operational burden.

Argo ducks this mistake, providing a robust scheduler and leveraging k8s for its executor.
This allows Argo to be managed independently of any of the workloads it manages - a huge step forwards over Airflow - but this comes at considerable ergonomic costs for trivial tasks and provides a more limited scheduler.

Previously I developed a system which provided a much stronger DSL than Airflow's, but made the same key mistake of not decoupling execution from the scheduler/coordinator.
Calf is a sketch of a programming language and system with a nearly fully featured DSL, and decoupling between scheduling (control flow of programs) and execution of "terminal" actions.

In short, think a Py-Lisp where instead of doing FFI directly to the parent Python instance you do FFI by enqueuing a (potentially retryable!) request onto a shared cluster message bus, from which subscriber worker processes elsewhere provide request/response handling.
One could reasonably accuse this project of being an attempt to unify Erlang and a hosted Python to build a "BASH for distsys" tool while providing a multi-tenant execution platform that can be centrally managed.

## License

Copyright Reid 'arrdem' McKenzie, 3/5/2017.
Distributed under the terms of the MIT license.
See the included `LICENSE` file for more.
