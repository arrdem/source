# clusterctrl

This project is a rewrite of the `clusterctrl` tool provided by the 8086 consultancy for interacting with their ClusterCTRL and ClusterHAT line of Raspberry Pi backplane products.

It serves to factor out the underlying i²c driver common to the ClusterCTRL family of products, and aims to implement a far more idiomatic and better documented CLI tool over top of that driver.

## license

This software is published under the MIT License

Copyright (c) 2018 Chris Burton (8086 consultancy)
Copyright (c) 2021 Reid McKenzie
