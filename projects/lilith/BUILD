py_project(
    name = "lib",
    lib_deps = [
        py_requirement("lark"),
    ],
    test_deps = [
        py_requirement("hypothesis"),
    ],
)

zapp_binary(
    name = "lilith",
    main = "src/python/lilith/__main__.py",
    deps = [
        ":lib",
        py_requirement("lark"), # FIXME: Absolutely a zapp bug
        py_requirement("prompt_toolkit"),
    ],
)
