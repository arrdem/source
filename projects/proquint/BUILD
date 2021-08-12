py_project(
    name = "proquint",
    test_deps = [
        py_requirement("hypothesis"),
    ],
)

zapp_binary(
    name = "qint",
    main = "src/python/proquint/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        ":proquint",
    ],
)
