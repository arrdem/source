"""
The Flowmetal server entry point.
"""

from flowmetal import frontend, interpreter, scheduler, reaper

import click


@click.group()
def cli():
    pass


cli.add_command(frontend.cli, name="frontend")
cli.add_command(interpreter.cli, name="interpreter")
cli.add_command(scheduler.cli, name="scheduler")
cli.add_command(reaper.cli, name="reaper")


if __name__ == "__main__":
    cli()
