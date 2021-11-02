"""USB hub can be turned on/off on Cluster HAT and reset on CTRL"""

import click


@click.group()
def hub():
    pass


@hub.command("on")
def hub_on():
    pass


@hub.command("off")
def hub_off():
    pass


@hub.command("reset")
def hub_reset():
    pass
