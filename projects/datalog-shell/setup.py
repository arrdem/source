from setuptools import setup


setup(
    name="arrdem.datalog.shell",
    # Package metadata
    version="0.0.2",
    license="MIT",
    description="A shell for my datalog engine",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/datalog-shell",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],

    scripts=[
        "bin/datalog"
    ],
    install_requires=[
        "arrdem.datalog~=2.0.0",
        "prompt_toolkit==2.0.9",
        "yaspin==0.14.3",
    ],
)
