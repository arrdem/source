zapp_binary(
    name = "cram",
    shebang = "/usr/bin/env /usr/bin/python3.10",
    main = "src/python/cram/__main__.py",
    imports = [
        "src/python"
    ],
    deps = [
        "//projects/vfs",
        py_requirement("click"),
        py_requirement("toposort"),
    ]
)
