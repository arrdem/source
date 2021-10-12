py_project(
    name = "lib"
)

zapp_binary(
    name = "hatctl",
    main = "src/python/hatctl/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        ":lib",
        py_requirement("click"),
    ],
)
