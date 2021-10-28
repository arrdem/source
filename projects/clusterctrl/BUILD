py_project(
    name = "lib"
)

zapp_binary(
    name = "clusterctrl",
    main = "src/python/clusterctrl/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        ":lib",
        py_requirement("click"),
    ],
)
