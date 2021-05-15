#!/usr/bin/env python

from os import path

from setuptools import setup, find_namespace_packages


# Fetch the README contents
rootdir = path.abspath(path.dirname(__file__))
with open(path.join(rootdir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="calf",
    version="0.0.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(include=["calf.*"]),
    entry_points={
        "console_scripts": [
            # DSL testing stuff
            "calf-lex = calf.lexer:main",
            "calf-parse = calf.parser:main",
            "calf-read = calf.reader:main",
            "calf-analyze = calf.analyzer:main",
            "calf-compile = calf.compiler:main",
            # Client/server stuff
            "calf-client = calf.client:main",
            "calf-server = calf.server:main",
            "calf-worker = calf.worker:main",
        ]
    },
    install_requires=[
        "pyrsistent~=0.17.0",
    ],
    extra_requires={
        "node": [
            "flask~=1.1.0",
            "pyyaml~=5.4.0",
            "redis~=3.5.0",
        ],
    },
)
