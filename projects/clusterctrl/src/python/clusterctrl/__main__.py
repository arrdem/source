"""
Cluster Control

(c) 8086 Consultancy 2018-2020
(c) Reid D. 'arrdem' McKenzie 2021
"""


from .cmd.fan import fan
from .cmd.hub import hub
from .cmd.led import led
from .cmd.power import power
from .cmd.save import save

import click


# Usage
# clusterctl <cmd> [<devices>]
# Commands (cmd)
#   status               # shows status
#   maxpi                # returns max number of Pi Zeros we control
#   init                 # Init ClusterHAT
#   setorder <old> <new> # Set order on device <old> to <new>
#   getpath <device>     # Get USB path to Px

#
# Where <devices> is either a single Pi Zero "p1" or a list like "p1 p4 p7"
# from p1 to p<maxpi> (without the quotes), so to turn on P1, P5 and P9 you would use
# clusterctrl on p1 p5 p9
#
# <order> selects which Cluster CTRL devices matches that <order> number


@click.group()
def cli():
    pass


@cli.command()
def status():
    """Show status information for all available devices."""


@cli.command()
def maxpi():
    """Show the number of available/attached Pis."""


@cli.command()
def init():
    """Init ClusterHAT"""


cli.add_command(led)
cli.add_command(power)
cli.add_command(hub)
cli.add_command(fan)
cli.add_command(save)


if __name__ == "__main__":
    cli()
