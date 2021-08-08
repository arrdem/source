# Zapp
<img align="right" src="zapp.jpg" alt="Spaceman spiff sets his zorcher to shake and bake" width=250>

Zapp is a comically-named tool for making Python [zipapps](https://www.python.org/dev/peps/pep-0441/).

Zipapps or zapps as we call them (hence the raygun theme) are packagings of Python programs into zip files. It's
comparable to [Pex](https://github.com/pantsbuild/pex/), [Subpar](https://github.com/google/subpar/) and
[Shiv](https://github.com/linkedin/shiv/) in intent, but shares the most with Subpar in particulars as like subpar Zapp
is designed for use with Bazel (and is co-developed with appropriate Bazel build rules).

## A quick overview of zipapps

A Python zipapp is a file with two parts - a "plain" text file with a "shebang" specifying a Python interpreter, followed by a ZIP formatted archive after the newline.
This is (for better or worse) a valid ZIP format archive, as the specification does not preclude prepended data.

When Python encounters a zipapp, it assumes you meant `PYTHONPATH=your.zip <shebang> -m __main__`.
See [the upstream docs](https://docs.python.org/3/library/zipapp.html#the-python-zip-application-archive-format).
So not only must `zapp` generate a prefix script, it needs to insert a `__main__.py` that'll to your application.

## A quick overview of zapp

Zapp is really two artifacts - `zapp.bzl` which defines `rules_python` (`zapp_binary`, `zapp_test`) macros and implementations.
These Bazel macros work together with the `zappc` "compiler" to make producing zapps from Bazel convenient.

## A demo

So let's give zapp a spin

``` shellsession
$ cd projects/zapp/examples
$ cat BUILD
load("//projects/zapp:zapp.bzl",
     "zapp",
     "zapp_binary",
)

# ...

zapp_binary(
    name = "hello_deps",
    main = "hello.py",
    deps = [
        py_requirement("pyyaml"),
    ]
)

```

In this directory there's the `zapp` compiler itself, and a couple of `hello_*` targets that are variously zapped.
One uses `imports`, one is

Let's try `bazel build :hello`

``` shellsession
$ bazel build :hello_deps
bazel build :hello_deps
INFO: Analyzed target //projects/zapp/example:hello_deps (22 packages loaded, 70 targets configured).
INFO: Found 1 target...
INFO: From Building zapp file //projects/zapp/example:hello_deps:
{'manifest': {'entry_point': 'projects.zapp.example.hello',
              'prelude_points': ['zapp.support.unpack:unpack_deps'],
              'shebang': '/usr/bin/env python3',
              'sources': {'__init__.py': None,
                          'projects/__init__.py': None,
                          'projects/zapp/__init__.py': None,
                          'projects/zapp/example/__init__.py': None,
                          'projects/zapp/example/hello.py': 'projects/zapp/example/hello.py',
                          'zapp/__init__.py': None,
                          'zapp/manifest.json': 'bazel-out/k8-fastbuild/bin/projects/zapp/example/hello_deps.zapp-manifest.json',
                          'zapp/support/__init__.py': None,
                          'zapp/support/manifest.py': 'projects/zapp/src/python/zapp/support/manifest.py',
                          'zapp/support/unpack.py': 'projects/zapp/src/python/zapp/support/unpack.py'},
              'wheels': {'PyYAML-5.4.1-cp39-cp39-manylinux1_x86_64.whl':
                          {'hashes': [],
                           'source': 'external/arrdem_source_pypi/pypi__pyyaml/PyYAML-5.4.1-cp39-cp39-manylinux1_x86_64.whl'}},
              'zip_safe': True},
 'opts': {'debug': True,
          'manifest': 'bazel-out/k8-fastbuild/bin/projects/zapp/example/hello_deps.zapp-manifest.json',
          'output': 'bazel-out/k8-fastbuild/bin/projects/zapp/example/hello_deps'}}
Target //projects/zapp/example:hello_deps up-to-date:
  bazel-bin/projects/zapp/example/hello_deps
INFO: Elapsed time: 0.497s, Critical Path: 0.13s
INFO: 8 processes: 7 internal, 1 linux-sandbox.
INFO: Build completed successfully, 8 total actions
```

Here, I've got the `zapp` compiler configured to debug what it's doing.
This is a bit unusual, but it's convenient for peeking under the hood.

The manifest which `zapp` consumes describes the relocation of files (and wheels, more on that in a bit) from the Bazel source tree per python `import = [...]` specifiers to locations in the container/logical filesystem within the zip archive.

We can see that the actual `hello.py` file (known as `projects/zapp/hello.py` within the repo) is being mapped into the zip archive without relocation.

We can also see that a `PyYAML` wheel is marked for inclusion in the archive.

If we run the produced zipapp -

``` shellsession
$ bazel run :hello_deps
INFO: Analyzed target //projects/zapp/example:hello_deps (0 packages loaded, 0 targets configured).
INFO: Found 1 target...
Target //projects/zapp/example:hello_deps up-to-date:
  bazel-bin/projects/zapp/example/hello_deps
INFO: Elapsed time: 0.068s, Critical Path: 0.00s
INFO: 1 process: 1 internal.
INFO: Build completed successfully, 1 total action
INFO: Build completed successfully, 1 total action
 - /home/arrdem/.cache/zapp/wheels/PyYAML-5.4.1-cp39-cp39-manylinux1_x86_64.whl
 - /home/arrdem/.cache/bazel/_bazel_arrdem/6259d2555f41e1db0292a7d7f00f78ca/execroot/arrdem_source/bazel-out/k8-fastbuild/bin/projects/zapp/example/hello_deps
 - /usr/lib/python39.zip
 - /usr/lib/python3.9
 - /usr/lib/python3.9/lib-dynload
 - /home/arrdem/.virtualenvs/source/lib/python3.9/site-packages
hello, world!
I have YAML! and nothing to do with it. /home/arrdem/.cache/zapp/wheels/PyYAML-5.4.1-cp39-cp39-manylinux1_x86_64.whl/yaml/__init__.py
```

Here we can see that zapp when executed unpacked the wheel into a cache, inserted that cached wheel into the `sys.path`, and correctly delegated to our `hello.py` script, which was able to `import yaml` from the packaged wheel! 🎉

## License

Copyright Reid 'arrdem' McKenzie August 2021.

Published under the terms of the MIT license.
