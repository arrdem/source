py_library(
  name = "lib",
  srcs = glob(["src/python/**/*.py"]),
  imports = [
    "src/python",
  ],
)

py_pytest(
  name = "test",
  srcs = glob(["test/python/**/*.py"]),
  deps = [
    ":lib",
    py_requirement("hypothesis"),
  ],
)
