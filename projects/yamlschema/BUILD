py_library(
    name="yamlschema",
    srcs=glob(["src/python/**/*.py"]),
    imports=[
        "src/python",
    ],
    deps=[
        py_requirement("PyYAML"),
    ],
)

py_pytest(
    name="test_yamlschema",
    srcs=glob(["test/python/test_*.py"]),
    data=glob(["*.json", "*.yaml"]),
    deps=[
        ":yamlschema",
    ],
)
