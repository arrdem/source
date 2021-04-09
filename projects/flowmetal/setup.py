from setuptools import setup

setup(
    name="arrdem.flowmetal",
    # Package metadata
    version='0.0.0',
    license="MIT",
    description="A weird execution engine",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reid 'arrdem' McKenzie",
    author_email="me@arrdem.com",
    url="https://git.arrdem.com/arrdem/flowmetal",
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
        "flowmetal",
    ],
    entry_points={
        'console_scripts': [
            'iflow=flowmetal.repl:main'
        ],
    },
    install_requires=[
        'prompt-toolkit~=3.0.0',
    ],
    extras_require={
    }
)
