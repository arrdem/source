# Reid's monorepo

I've found it inconvenient to develop lots of small Python modules.
And so I'm going the other way; Bazel in a monorepo with subprojects so I'm able to reuse a maximum of scaffolding.

## Projects

- [Datalog](projects/datalog) and the matching [shell](projects/datalog-shell)
- [YAML Schema](projects/yamlschema) (JSON schema with knowledge of PyYAML's syntax structure & nice errors)
- [Zapp! (now with a new home and releases)](https://github.com/arrdem/rules_zapp)
- [Flowmetal](projects/flowmetal)
- [Lilith](projects/lilith)

## Hacking (Ubuntu)

See [HACKING.md](HACKING.md)

## License

Copyright Reid 'arrdem' McKenzie, 4/8/2021.

Unless labeled otherwise, the contents of this repository are distributed under the terms of the MIT license.
See the included `LICENSE` file for more.
