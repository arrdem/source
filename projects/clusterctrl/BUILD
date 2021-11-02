py_project(
    name = "lib",
    lib_deps = [
        py_requirement("smbus2"),
    ],
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
