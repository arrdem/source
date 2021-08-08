load("//projects/zapp:zapp.bzl",
     "zapp_binary",
)

zapp_binary(
    name = "hello_script",
    main = "hello.py",
    # entry_point is inferred from main =
)

zapp_binary(
    name = "hello_deps",
    main = "hello.py",
    # deps also get zapped via their underlying wheels
    deps = [
        py_requirement("pyyaml"),
    ]
)
