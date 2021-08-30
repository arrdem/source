#!/usr/bin/env python3

"""
A quick and dirty XML formatter.
"""

from bs4 import BeautifulSoup
import click


@click.command()
@click.argument("filename")
def main(filename):
    with open(filename) as f:
        bs = BeautifulSoup(f, "xml")

    with open(filename, "w") as of:
        of.write(bs.prettify())
        of.write("\n")

    print(f"Formatted {filename}!")


if __name__ == "__main__":
    main()
