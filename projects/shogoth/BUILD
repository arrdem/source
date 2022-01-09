py_library(
    name = "lib",
    srcs = glob(["src/python/**/*"]),
    imports = [
        "src/python"
    ],
    deps = [
        py_requirement("lark"),
    ],
)

zapp_binary(
    name = "shogothd",
    main = "src/python/shogoth/server/__main__.py",
    deps = [
        ":lib",
    ],
)

zapp_binary(
    name = "shogoth",
    main = "src/python/shogoth/client/__main__.py",
    deps = [
        ":lib",
    ],
)

zapp_binary(
    name = "repl",
    main = "src/python/shogoth/repl/__main__.py",
    shebang = "/usr/bin/env python3.10",
    deps = [
        ":lib",
    ]
)
