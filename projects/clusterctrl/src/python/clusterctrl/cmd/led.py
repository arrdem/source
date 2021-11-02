"""Enable or disable all status LEDs."""

import click


@click.group()
def led():
    pass


@led.command("on")
def led_on():
    pass


@led.command("off")
def led_off():
    pass
