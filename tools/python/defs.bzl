load("@arrdem_source_pypi//:requirements.bzl",
     _py_requirement = "requirement"
)

load("@rules_python//python:defs.bzl",
     _py_binary = "py_binary",
     _py_test = "py_test",
     _py_library = "py_library",
)


def py_requirement(*args, **kwargs):
    """A re-export of requirement()"""
    return _py_requirement(*args, **kwargs)


def py_test(python_version=None, **kwargs):
    """A re-export of py_test()"""

    if python_version and python_version != "PY3":
        fail("py3k only!")

    return _py_test(
        python_version="PY3",
        **kwargs,
    )


def py_pytest(name, srcs, deps, main=None, python_version=None, args=None, **kwargs):
    """A py_test target which uses pytest."""

    if python_version and python_version != "PY3":
        fail("py3k only!")

    f = "//tools/python:bzl_pytest_shim.py"

    deps = [
        py_requirement("pytest"),
        py_requirement("jedi"),
        py_requirement("pytest-pudb"),
    ] + deps

    srcs = [f] + srcs

    t = py_test(
      name = name,
      srcs = srcs,
      main = f,
      args = args,
      python_version="PY3",
      deps = deps,
      **kwargs,
    )

    # FIXME (arrdem 2020-09-27):
    #   This really needs to be a py_image_test.
    #   Not clear how to achieve that.
    # py_image(
    #   name = name + ".containerized",
    #   main = f,
    #   args = args,
    #   srcs = srcs,
    #   deps = deps,
    #   **kwargs,
    # )

    return t


def py_unittest(srcs=[], **kwargs):
    """A helper for running unittest tests"""

    f = "//tools/python:bzl_unittest_shim.py"
    return py_test(
        main = f,
        srcs = [f] + srcs,
        **kwargs
    )


def py_binary(python_version=None, main=None, srcs=None, **kwargs):
    """A re-export of py_binary()"""

    if python_version and python_version != "PY3":
        fail("py3k only!")

    srcs = srcs or []
    if main not in srcs:
        srcs = [main] + srcs

    return _py_binary(
        python_version = "PY3",
        main = main,
        srcs = srcs,
        **kwargs,
    )


def py_library(srcs_version=None, **kwargs):
    """A re-export of py_library()"""

    if srcs_version and srcs_version != "PY3":
        fail("py3k only!")

    return _py_library(
        srcs_version="PY3",
        **kwargs
    )


ResourceGroupInfo = provider(
    fields = {
        "srcs": "files to use from Python",
    },
)


def _resource_impl(ctx):
    srcs = []
    for target in ctx.attr.srcs:
        srcs.extend(target.files.to_list())
    transitive_srcs = depset(direct = srcs)

    return [
        ResourceGroupInfo(
            srcs = ctx.attr.srcs,
        ),
        PyInfo(
            has_py2_only_sources = False,
            has_py3_only_sources = True,
            uses_shared_libraries = False,
            transitive_sources = transitive_srcs,
        ),
    ]

py_resources = rule(
    implementation = _resource_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_empty = True,
            mandatory = True,
            allow_files = True,
            doc = "Files to hand through to Python",
        ),
    },
)

def py_project(name=None,
               lib_srcs=None,
               lib_deps=None,
               test_srcs=None,
               test_deps=None):
    """
    A helper for defining conventionally-formatted python project.

    Assumes that there's a src/python tree, and a src/test tree.

    Each test_*.py source generates its own implicit test target. This allows
    for automatic test parallelism.

    """

    lib_srcs = lib_srcs or native.glob(["src/python/**/*.py"])
    test_srcs = test_srcs or native.glob(["test/python/**/*.py"])

    py_library(
        name=name,
        srcs=lib_srcs,
        deps=lib_deps,
        imports=["src/python"],
    )

    for src in test_srcs:
        if "test_" in src:
            py_pytest(
                name=name + ".test." + str(hash(src)).replace("-", "") + "." + src.split("/")[-1],
                srcs=test_srcs,
                deps=[name] + test_deps,
                imports=["test/python"],
            )
