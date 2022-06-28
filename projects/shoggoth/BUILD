py_project(
    name = "shoggoth",
    main = "src/python/shoggoth/repl/__main__.py",
    main_deps = [
        py_requirement("prompt_toolkit"),
        py_requirement("yaspin"),
        py_requirement("pyrsistent"),
    ],
    lib_deps = [
        py_requirement("lark"),
        py_requirement("flask"),
    ],
)

zapp_binary(
    name="ichor",
    main = "src/python/ichor/__main__.py",
    shebang="/usr/bin/env python3",
    deps = [
        ":lib",
    ],
)
