py_project(
    name = "jobq",
    lib_deps = [
        "//projects/anosql",
        "//projects/anosql-migrations",
    ]
)

zapp_binary(
    name = "benchmark",
    main = "benchmark.py",
    deps = [":jobq"],
)
