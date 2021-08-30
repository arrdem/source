load("@arrdem_source_pypi//:requirements.bzl",
     _py_requirement = "requirement"
)

load("@rules_python//python:defs.bzl",
     "py_runtime",
     "py_runtime_pair",
     _py_binary = "py_binary",
     _py_test = "py_test",
     _py_library = "py_library",
)

load("@rules_zapp//zapp:zapp.bzl",
     "zapp_binary",
)

load("//tools/flake8:flake8.bzl",
     "flake8",
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
               main=None,
               main_deps=None,
               lib_srcs=None,
               lib_deps=None,
               lib_data=None,
               test_srcs=None,
               test_deps=None,
               test_data=None):
    """
    A helper for defining conventionally-formatted python project.

    Assumes that there's a {src,test}/{resources,python} where src/ is a library and test/ is local tests only.

    Each test_*.py source generates its own implicit test target. This allows for automatic test parallelism. Non
    test_*.py files are implicitly srcs for the generated test targets. This is the same as making them implicitly a
    testonly lib.

    """

    lib_srcs = lib_srcs or native.glob(["src/python/**/*.py"],
                                       exclude=[
                                           "**/*.pyc",
                                       ])
    lib_data = lib_data or native.glob(["src/resources/**/*",
                                        "src/python/**/*"],
                                       exclude=[
                                           "**/*.py",
                                           "**/*.pyc",
                                       ])
    test_srcs = test_srcs or native.glob(["test/python/**/*.py"],
                                         exclude=[
                                             "**/*.pyc",
                                         ])
    test_data = test_data or native.glob(["test/resources/**/*",
                                          "test/python/**/*"],
                                         exclude=[
                                             "**/*.py",
                                             "**/*.pyc",
                                         ])

    lib_name = name if not main else "lib"

    py_library(
        name=lib_name,
        srcs=lib_srcs,
        deps=lib_deps,
        data=lib_data,
        imports=[
            "src/python",
            "src/resources",
        ],
        visibility = [
            "//visibility:public",
        ],
    )

    # if lib_srcs:
    #     flake8(
    #         name = "flake8",
    #         deps = [lib_name],
    #     )

    if main:
        py_binary(
            name=name,
            main=main,
            deps=(main_deps or []) + [lib_name],
            imports=[
                "src/python",
                "src/resources",
            ],
            visibility = [
                "//visibility:public",
            ],
        )

        zapp_binary(
            name=name + ".zapp",
            main=main,
            deps=(main_deps or []) + [lib_name],
            data=lib_data,
            imports=[
                "src/python",
                "src/resources",
            ],
            visibility = [
                "//visibility:public",
            ],
        )

    for src in test_srcs:
        if "test_" in src:
            py_pytest(
                name=src.split("/")[-1],
                srcs=[src] + [f for f in test_srcs if "test_" not in f],
                deps=[lib_name] + (test_deps or []),
                data=test_data,
                imports=[
                    "test/python",
                    "test/resources",
                ],
            )
