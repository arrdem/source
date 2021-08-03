from setuptools import setup


setup(
    name="arrdem.kook",
    # Package metadata
    version="0.1.19",
    license="MIT",
    description="A Kazoo based inventory management system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/kook",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    # Package setup
    package_dir={"": "src"},
    packages=[
        "kook",
    ],
    scripts=[
        "bin/kook",
        "bin/kook-inventory",
    ],
    install_requires=[
        "kazoo>=2.6.1",
        "toolz>=0.10.0",
        "PyYAML>=5.1.0",
        "Jinja2>=2.11.0",
    ],
    extras_require={"color": ["colored>=1.4.2"]},
)
