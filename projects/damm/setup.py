from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="arrdem.damm",
    version="0.1.0",
    description="An implementation of Damm check digits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arrdem/source",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    classifiers=[
        # Optional
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.9",
    ],
    packages=[
        "damm",
    ],
    package_dir={"": "src/python"},
    python_requires=">=3.9",
    extras_require={  # Optional
        "dev": ["check-manifest"],
        "test": ["pytest", "hypothesis"],
    },
)
