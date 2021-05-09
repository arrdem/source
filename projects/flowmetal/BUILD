package(default_visibility = ["//visibility:public"])

py_library(
    name = "lib",
    srcs = [
        "src/python/**/*.py"
    ],
    imports = ["src/python"],
    deps = [
    ]
)

py_binary(
    name = "server",
    deps = [
        ":lib",
        py_requirement("click"),
        py_requirement("redis"),
    ],
    main = "src/python/flowmetal/server/__main__.py",
)
