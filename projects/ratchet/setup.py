from setuptools import setup


setup(
    name="arrdem.ratchet",
    # Package metadata
    version="0.0.0",
    license="MIT",
    description="A 'ratcheting' message system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/ratchet",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    # Package setup
    package_dir={"": "src/python"},
    packages=[
        "ratchet",
    ],
    entry_points={},
    install_requires=[],
    extras_require={},
)
