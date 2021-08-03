from setuptools import setup


setup(
    name="arrdem.overwatch",
    # Package metadata
    version="0.0.7",
    license="MIT",
    description="A Kook backed inventory monitoring syste",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/overwatch",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    # Package setup
    scripts=[
        "bin/overwatchd",
    ],
    install_requires=[
        "arrdem.kook>=0.1.0",
        "kazoo>=2.6.1",
        "PyYaml>=5.1.2",
    ],
)
