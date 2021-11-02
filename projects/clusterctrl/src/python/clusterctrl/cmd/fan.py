"""Turns FAN on/off for CTRL with <order>."""

import click


@click.group()
def fan():
    pass


@fan.command("on")
def fan_on():
    pass


@fan.command("off")
def fan_off():
    pass
