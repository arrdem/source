#!/usr/bin/env python3

# alert on [<devices>]	# Turns on all ALERT LED or for pX devices
# alert off [<devices>]	# Turns off all ALERT LED or for pX devices

import click


@click.group()
def alert():
    pass


@alert.command("on")
def alert_on():
    pass


@alert.command("off")
def alert_off():
    pass
