from setuptools import setup

setup(
    name="arrdem.lilith",
    # Package metadata
    version="0.0.0",
    license="MIT",
    # Package setup
    package_dir={"": "src/python"},
    packages=[
        "lilith",
    ],
    install_requires=[
        "lark",
    ],
    test_requires=[
        "pytest",
        "hypothesis",
    ],
)
