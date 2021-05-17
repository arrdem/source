from setuptools import setup

setup(
    name="arrdem.yamlschema",
    # Package metadata
    version="0.1.0",
    license="MIT",
    description="Detailed JSON schema validation for YAML",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://github.com/arrdem/source",
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
        "yamlschema",
    ],
    install_requires=[
        "PyYAML~=5.4.1",
    ],
)
