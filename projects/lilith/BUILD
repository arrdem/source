py_project(
    name = "lilith",
    lib_deps = [
        py_requirement("lark"),
    ],
    test_deps = [
        py_requirement("hypothesis"),
    ]
)

py_binary(
    name = "repl",
    main = "src/python/lilith/repl.py",
    imports = [
        "src/python",
    ],
    deps = [
        ":lilith",
        py_requirement("prompt_toolkit"),
    ]
)
