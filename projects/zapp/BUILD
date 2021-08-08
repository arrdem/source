package(default_visibility = ["//visibility:public"])

load("zapp.bzl",
     "zapp_binary",
)

# Bootstrapping Zapp using py_binary
py_binary(
    name = "zappc",
    main = "src/python/zapp/compiler/__main__.py",
    imports = [
        "src/python",
    ],
)

# Zapp plugins used as a runtime library by rules_zapp
py_library(
    name = "zapp_support",
    srcs = glob(["src/python/zapp/support/**/*.py"]),
    imports = [
        "src/python",
    ],
)

# Zapped zapp
zapp_binary(
    name = "zapzap",
    main = "src/python/zapp/__main__.py",
    imports = [
        "src/python",
    ],
)
