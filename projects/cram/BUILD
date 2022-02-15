py_library(
    name = "lib",
    srcs = glob(["src/python/**/*.py"]),
    deps = [
        "//projects/vfs",
        py_requirement("click"),
        py_requirement("toposort"),
        py_requirement("toml"),
    ]
)

zapp_binary(
    name = "cram",
    main = "src/python/cram/__main__.py",
    shebang = "/usr/bin/env python3",
    imports = [
        "src/python"
    ],
    deps = [
        ":lib",
    ],
)

sh_test(
    name = "test_cram",
    srcs = glob(["test.sh"]),
    data = glob(["test/**/*"]) + [":cram"],
)
