#!/usr/bin/env python3

# save all <order>		# Save current settings to EEPROM
# save order <order>	# Save current "order" setting to EEPROM
# save usbboot <order>	# Save current USBBOOT settings to EEPROM
# save pos <order>	# Save current Power On State to EEPROM
# save defaults <order>	# Save default settings to EEPROM

import click


@click.group()
def save():
    pass


@save.command("all")
def save_all():
    pass


@save.command("order")
def save_order():
    pass


@save.command("usbboot")
def save_usbboot():
    pass


@save.command("power")
def save_power():
    pass


@save.command("defaults")
def save_defaults():
    pass
