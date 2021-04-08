"""
Platform independent sorting/formatting for requirements.txt
"""

import re

import click

REQ_PATTERN = re.compile(
    r"(?P<pkgname>[a-zA-Z0-9_-]+)(?P<features>\[.*?\])?==(?P<version>[^\s;#]+)|(.*?#egg=(?P<eggname>[a-zA-Z0-9_-]+))"
)


SHITLIST = [
    "pip",
    "pkg-resources",
    "setuptools",
]


def sort_key(requirement: str) -> str:
    requirement = requirement.lower()
    match = re.match(REQ_PATTERN, requirement)
    sort_key = (
        (match.group("pkgname") or match.group("eggname"))  # Get the match group
        .replace("-", "")  # We ignore -
        .replace("_", "")  # And _
    )
    return sort_key


@click.command()
@click.option("--execute/--dryrun", "execute", default=False)
@click.argument("requirements")
def main(requirements, execute):
    """Given the path of a requirements.txt, format it.

    If running in --execute, rewrite the source file with sorted contents and exit 0.

    If running in --dryrun, exit 0 if --execute would produce no changes otherwise exit 1.

    """

    with open(requirements) as f:
        lines = f.readlines()
        f.seek(0)
        # Preserve an initial "buffer" for equality testing
        initial_buff = f.read()

    # Trim whitespace
    lines = [l.strip() for l in lines]

    # Discard comments and shitlisted packages
    lines = [l for l in lines if not l.startswith("#") and not sort_key(l) in SHITLIST]

    # And sort, ignoring case explicitly
    lines = sorted(lines, key=sort_key)

    # And generate a new "buffer"
    new_buff = "\n".join(lines) + "\n"

    if new_buff != initial_buff and not execute:
        exit(1)

    else:
        with open(requirements, "w") as f:
            f.write(new_buff)
        exit(0)


if __name__ == "__main__":
    main()
