import click


# power on [<devices>]  # Turn on All Pi Zero or devices
# power off [<devices>] # Turn off All Pi Zero or devices


@click.group()
def power():
    pass


@power.command("on")
@click.argument("devices", nargs="*")
def power_on(devices):
    """Power on selected devices."""


@power.command()
@click.argument("devices", nargs="*")
def power_off(devices):
    """Power off selected devices."""
