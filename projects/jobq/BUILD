zapp_binary(
    name = "jobq",
    main = "src/python/jobq/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        "//projects/anosql",
        "//projects/anosql-migrations",
        py_requirement("flask"),
        py_requirement("pyyaml"),
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
