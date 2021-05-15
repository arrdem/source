py_library(
    name="yamlschema",
    srcs=[
        "yamlschema.py",
    ],
    imports=[
        ".",
    ],
    deps=[
        py_requirement("PyYAML"),
    ],
)

py_pytest(
    name="test_yamlschema",
    srcs=glob(["test_*.py"]),
    data=glob(["*.json", "*.yaml"]),
    deps=[
        ":yamlschema",
    ],
)
