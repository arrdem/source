zapp_binary(
    name = "jobqd",
    main = "src/python/jobqd/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        "//projects/jobq",
        py_requirement("flask"),
    ]
)

py_library(
    name = "client",
    srcs = [
        "src/python/jobq/rest/api.py",
    ],
    imports = [
        "src/python",
    ],
    deps = [
        py_requirement("requests"),
    ],
)
