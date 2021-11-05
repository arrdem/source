# clusterctrl

This project is a clean-sheet rewrite of the `clusterctrl` tool and underlying device driver provided by the 8086 consultancy for interacting with their ClusterCTRL and ClusterHAT line of Raspberry Pi backplane products.

## Usage & driver API

``` python
from clusterctrl.driver import ClusterCTRLv2Driver as Driver
from smbus2 import SMBus

hat = Driver(SMBus(3))  # Note that 3 here is the number of the i2c device the HAT is on
```

A quick API overview -

The CTRL/HAT products "order" themselves (identify boards) using an EEPROM stored value called 'order'.
The official clients use "order" to enable for somewhat stable sequential addressing of "pi6" as being board 2 pi 1.
However it's far more general purpose and predictable to directly expose and model the device tree.

Note that the firmware default for "order" is `20` and this driver will automatically assign random IDs to boards with orders of 20.
This behavior can be disabled by subclassing the driver and overloading `_post_init()`.

This API is built atop a `PiRef(board_id, pi_id)` tuple which is intended to allow for the construction of cluster management APIs which allow for automatic but predictable mapping of requests (eg. `power_on`, `power_status`) to a given device.

If you provide an "unqualified" integer ID directly, the driver will attempt to interpret it as being in `[min_pi, max_pi]` specific to this device.

``` python
hat.fw_version  # => (1, 6)
hat.min_pi      # => <PiRef XXX-01>
hat.max_pi      # => <PiRef XXX-05>
hat.pis()       # => Iterable[PiRef] (iterate over all Pis on this device in order)
hat.type        # => BoardType
hat.max_adc     # => int (ADC support is incomplete)
```

### Power status

``` python
hat.power_on(Union[int, PiRef])
hat.power_off(Union[int, PiRef])
hat.power_status(Union[int, PiRef])

hat.power_all_off()
hat.power_all_on()

hat.eeprom_save_powerstate()
```

### Board identification

``` python
hat.get_order()
hat.set_order(<order: uint8>)

hat.eeprom_save_order()
```

### Alert lights

``` python
hat.alert_on()
hat.alert_off()

hat.led_on()
hat.led_off()

hat.eeprom_save_leds()
```

### Fan control

``` python
hat.fan_on()
hat.fan_off()
hat.fan_status()

hat.read_temp()  # Temp in integer kelvin
```

### USB hub control

``` python
hat.hub_on()
hat.hub_off()
hat.hub_reset()
```

### USB booting

**WARNING**: Support for USB booting is specific to the ClusterHAT family of devices, to which I don't have access.
As such no promises can be made for whether this machinery does what it's supposed to do.
The upstream drivers have a lot of oddities around USB booting and ClusterHAT specific use of GPIO pins.

``` python
hat.usbboot_on()
hat.usbboot_off()
hat.usbboot_status()
hat.eeprom_save_usbboot()
```

#### Driver.eeprom_reset
Reset all EEPROM stored settings to their 'factory' firmware defaults.

#### Driver.eeprom_save_all
Save all values back to EEPROM.
Note that this does not update the defaults restored by `Driver.eeprom_reset`.

## license

Copyright (c) 2021 Reid McKenzie

This software is published under the terms of the MIT License
