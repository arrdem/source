py_project(
    name = "lib",
    lib_deps = [
        py_requirement("lark"),
        py_requirement("pyyaml"),
        py_requirement("markdown"),
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
        # FIXME: Due to zapp bug(s), replicating requirements here.
        py_requirement("lark"),
        py_requirement("pyyaml"),
        py_requirement("markdown"),
        py_requirement("prompt_toolkit"),
    ],
)
