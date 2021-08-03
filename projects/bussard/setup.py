from setuptools import setup


setup(
    name="arrdem.bussard",
    # Package metadata
    version="0.0.0",
    license="MIT",
    description="A DNS zonefile engine",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/bussard",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    # Package setup
    package_dir={"": "src/python"},
    packages=[
        "bussard",
    ],
    scripts=[
        "src/python/bussard/bfmt",
        "src/python/bussard/bparse",
    ],
)
