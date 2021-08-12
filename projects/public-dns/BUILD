zapp_binary(
    name = "updater",
    main = "src/python/arrdem/updater/__main__.py",
    imports = [
        "src/python",
    ],
    deps = [
        "//projects/gandi",
        py_requirement("jinja2"),
        py_requirement("pyyaml"),
        py_requirement("meraki"),
    ],
)
