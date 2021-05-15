package(default_visibility = ["//visibility:public"])

py_library(
    name = "lib",
    srcs = glob(["src/python/flowmetal/*.py"]),
    imports = [
        "src/python"
    ],
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
    main = "src/python/flowmetal/__main__.py",
)
