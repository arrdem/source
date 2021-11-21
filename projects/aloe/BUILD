py_project(
    name = "lib"
)

zapp_binary(
    name = "aloe",
    main = "src/python/aloe/__main__.py",
    deps = [
        ":lib",
        py_requirement("graphviz"),
        py_requirement("icmplib"),
        py_requirement("requests"),
    ],
)
