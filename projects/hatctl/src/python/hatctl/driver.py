"""An I2C driver for the ClusterCTRL/ClusterHAT device(s)."""

from enum import Enum
from itertools import chain, repeat
from time import sleep
from typing import Union

import smbus


def once(f):
    """Decorator. Defer to f once and only once, caching the result forever.

    Users with a functional background may recognize the concept of a `thunk`.

    """

    unset = val = object()
    def _helper(*args, **kwargs):
        nonlocal val
        if val is unset:
            val = f(*args, **kwargs)
        return val

    return _helper


# I2C address of ClusterCTRL device
I2C_ADDRESS = 0x20


class BoardType(Enum):
    DA = 0x00      # Unknown, presunably a prototype
    A6 = 0x03      # https://clusterctrl.com/p/aplus6
    STACK = 0x04   # https://shop.pimoroni.com/products/clusterctrl-stack
    SINGLE = 0x01  # Do the 'single' and 'triple' really use the same board ID?
    TRIPLE = 0x01
    PHAT = 0x02


class Status(Enum):
    """Values of the Reg.STATUS register."""

    OKAY = 0
    UNSUPPORTED = 1
    NO_PI = 2
    UNKNOWN = 3
    RESET_FAILED = 4


class Reg(Enum):
    """The registers supported by an Cluster device."""

    # https://github.com/burtyb/ClusterCTRL/blob/54bd6c4593e99decbf5a4953c794775b8c4db022/src/main.c#L380-L403
    VERSION = 0x00  # Register layout version
    MAXPI = 0x01  # Maximum number of Pi
    ORDER = 0x02  # Order - used to sort multiple ClusterCTRL devices
    MODE = 0x03  # N/A
    TYPE = 0x04  # 0=DA, 1=pHAT
    DATA7 = 0x05  #
    DATA6 = 0x06  #
    DATA5 = 0x07  #
    DATA4 = 0x08  #
    DATA3 = 0x09  #
    DATA2 = 0x0A  #
    DATA1 = 0x0B  #
    DATA0 = 0x0C  #
    CMD = 0x0D  # Command
    STATUS = 0x0E  # Status


class Cmd(Enum):
    """Commands supported by various Cluster devices."""

    # https://github.com/burtyb/ClusterCTRL/blob/54bd6c4593e99decbf5a4953c794775b8c4db022/src/main.c#L405-L434
    ON = 0x03  # Turn on Px (data0=x)
    OFF = 0x04  # Turn off Px (data0=x)
    ALERT_ON = 0x05  # Turn on Alert LED
    ALERT_OFF = 0x06  # Turn off Alert LED
    HUB_CYCLE = 0x07  # Reset USB HUB (turn off for data0*10ms, then back on)
    HUB_ON = 0x08 # Turn on the USB hub
    HUB_OFF = 0x09 # Turn off the USB hub
    LED_EN = 0x0A  # Enable Px LED (data0=x) (PHAT only)
    LED_DIS = 0x0B  # Disable Px LED (data0=x) (PHAT only)
    PWR_ON = 0x0C  # Turn off PWR LED
    PWR_OFF = 0x0D  # Turn off PWR LED
    RESET = 0x0E  # Resets ClusterCTRL (does not keep power state)
    GET_PSTATUS = 0x0F  # Get Px power status (data0=x)
    FAN = 0x10  # Turn fan on (data0=1) or off (data0=0)
    GETPATH = 0x11  # Get USB path to Px (data0=x 0=controller) returned in data7-data0
    USBBOOT_EN = 0x12  # Turn on USBBOOT
    USBBOOT_DIS = 0x13  # Turn off USBBOOT
    GET_USTATUS = 0x14  # Get Px USBBOOT status (data0=x)
    SET_ORDER = 0x15  # Set order (data0=order)
    SAVE = 0xF0  # Save current PWR/P1-LED/P2-LED/P1/P2/Order/Mode to EEPROM
    SAVEDEFAULTS = 0xF1  # Save factory defaults
    GET_DATA = 0xF2  # Get DATA (Temps/ADC/etc.)
    SAVE_ORDER = 0xF3  # Save order to EEPROM
    SAVE_USBBOOT = 0xF4  # Save usbboot status to EEPROM
    SAVE_POS = 0xF5  # Save Power On State to EEPROM
    SAVE_LED = 0xF6  # Save LED to EEPROM
    NOP = 0x90  # Do nothing


class Data(Enum):
    """Datum that can be read back from the Cluster device via Cmd.GET_DATA"""

    # Get arbitrary data from ClusterCTRL
    VERSION = 0x00  # Get firmware version
    ADC_CNT = 0x01  # Returns number of ADC ClusterCTRL supports
    ADC_READ = 0x02  # Read ADC data for ADC number 'data0'
    ADC_TEMP = 0x03  # Read Temperature ADC
    FANSTATUS = 0x04  # Read fan status


class ClusterCTRLDriver(object):
    def __init__(self, bus: smbus.SMBus, address: int = I2C_ADDRESS, delay: int = 0, clear = False):
        """Initialize a ClusterCTRL/ClusterHAT driver instance for a given bus device."""
        self._bus = bus
        self._address = address
        self._delay = delay
        self._clear = clear

    def _read(self, id: Union[Reg, Data], len: int = 1):
        """A convenient abstraction for reading data back."""

        # Performing a "fundamental" read
        if isinstance(id, Reg):
            if len == 1:
                return self._bus.read_byte_data(self._address, id.value)
            else:
                return self._bus.read_block_data(self._address, id.value, len)

        # Performing a "command" read
        elif isinstance(id, Data):
            return self._call(Cmd.GET_DATA, id.value)

    def _write(self, id: Reg, val: int):
        """A convenient abstraction for writing a register."""

        return self._bus.write_byte_data(self._address, id.value, val)

    def _call(self, op: Cmd, *args, clear = False):
        """A convenient abstraction over the 'calling' convention for ops.

        Operations are "called" when Reg.CMD is written to.
        Operations consume parameters from Reg.DATA0-Reg.DATA7.

        If `clear=` is truthy, any registers not defined by parameters will be cleared (zeroed) as a safety measure.

        Note that the caller is responsible for reading any returned data, for which the protocol is less clear.
        Most operations "just" return via reg.DATA0, but some don't.

        """

        if self._clear or clear:
            args = chain(args, repeat(0))

        args = zip([Reg.DATA0, Reg.DATA1, Reg.DATA2, Reg.DATA3, Reg.DATA4, Reg.DATA5, Reg.DATA6, Reg.DATA7], args)
        for r, v in args:
            self._write(r, v)

        # Execute the call
        self._write(Reg.CMD, op.value)

        # If the user has specified a delay, sleep
        if self._delay:
            sleep(self._delay)

        if self._read(Reg.STATUS) == 1:  # Status error: Unsupported
            raise Exception("Command %s appears not to be supported by the board" % op)

        # Return the (mostly) meaningful return code
        return self._read(Reg.DATA0)

    @property
    def min_pi(self):
        """Get the minimum supported Pi ID on this controller."""

        return 1

    @property
    @once
    def max_pi(self):
        """Get the maximum supported Pi ID on this controller."""

        return self._read(Reg.MAXPI)

    @property
    def pi_ids(self):
        """Iterate over the IDs of Pis which could be connected to this controller."""

        return range(self.min_pi, self.max_pi + 1)

    @property
    def type(self) -> BoardType:
        return BoardType(self._read(Reg.TYPE))

    @property
    def fw_version(self):
        self._read(Data.VERSION)
        return (self._read(Reg.DATA1), self._read(Reg.DATA0))

    def reset_all(self):
        """[Power] cycle the entire Controller."""

        return self._call(Cmd.RESET)

    ####################################################################################################
    # EEPROM management
    ####################################################################################################
    def eeprom_save_all(self):
        """Persist all supported options to EEPROM."""

        return self._call(Cmd.SAVE)

    def eeprom_reset(self):
        """Reset EEPROM to factory/firmware default value(s)."""

        return self._call(Cmd.SAVEDEFAULTS)

    def eeprom_save_powerstate(self):
        """Persist the current power state to EEPROM."""

        return self._call(Cmd.SAVE_POS)

    def eeprom_save_leds(self):
        """Persist the current LED state to EEPROM."""

        return self._call(Cmd.SAVE_LED)

    def eeprom_save_order(self):
        """Persist the current order value to EEPROM."""

        return self._call(Cmd.SAVE_ORDER)

    def eeprom_save_usbboot(self):
        """Persist USB booting settings to EEPROM."""

        return self._call(Cmd.SAVEUSBBOOT)

    ####################################################################################################
    # USB hub management
    ####################################################################################################
    def hub_on(self):
        """Turn on the USB hub."""

        return self._call(Cmd.HUB_ON)

    def hub_off(self):
        """Turn off the USB hub."""

        return self._call(Cmd.HUB_ON)

    # FIXME: Is hub_status unsupported in the firmware?

    def reset_hub(self, delay: int = 0):
        """[Power] cycle the Controller hub for `delay` x 10ms."""

        return self._call(Cmd.HUB_CYCLE, delay)

    ####################################################################################################
    # Power management
    ####################################################################################################
    def power_on(self, id: int):
        """Power on a given slot by ID."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.ON, id)

    def power_off(self, id: int):
        """Power off a given slot by ID."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.OFF, id)

    def power_status(self, id: int):
        """Read the status of a given slot by ID."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.GET_PSTATUS, id)

    def power_all_on(self):
        """Power on all slots in this Controller."""

        for id in self.pi_ids:
            if not self.power_status(id):
                self.power_on(id)

    def power_all_off(self):
        """Power off all slots in this Controller."""

        for id in self.pi_ids:
            self.power_off(id)

    ####################################################################################################
    # LED management
    ####################################################################################################
    def alert_on(self):
        """Turn on the alert LED on the Controller."""

        return self._call(Cmd.ALERT_ON)

    def alert_off(self):
        """Turn off the alert LED on the Controller."""

        return self._call(Cmd.ALERT_OFF)

    ####################################################################################################
    # LED management
    ####################################################################################################
    def fan_on(self):
        """Turn on the fan(s) attached to this Controller."""

        return self._call(Cmd.FAN, 1)

    def fan_off(self):
        """Turn off the fan(s) attached to this Controller."""

        return self._call(Cmd.FAN, 0)

    def fan_status(self):
        """Get the status of the fan(s) attached to this Controller."""

        return self._read(Data.FANSTATUS)

    ####################################################################################################
    # 'order' (board ID) management
    ####################################################################################################
    def get_order(self):
        """Get the 'order' value of this device. Can be updated via """

        return self._read(Reg.ORDER)

    def set_order(self, order: int):
        """Set an 'order' (Controller ID) value."""

        assert 0 < order <= 255
        return self._call(Cmd.SET_ORDER, order)

    ####################################################################################################
    # USB booting
    ####################################################################################################
    def usbboot_on(self, id: int):
        """Enable USB booting for the given Pi."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.USBBOOT_EN, id)

    def usbboot_off(self, id: int):
        """Disable USB booting for the given Pi."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.USBBOOT_DIS, id)

    def usbboot_status(self, id: int):
        """Get the current USB booting status for the given Pi."""

        assert 0 < id <= self.max_pi
        return self._call(Cmd.GET_USTATUS, id)

    ####################################################################################################
    # ADCs
    ####################################################################################################
    @property
    @once
    def max_adc(self):
        return self._read(Data.ADC_CNT)

    @property
    def adc_ids(self):
        return range(1, self.max_adc + 1)

    def read_adc(self, id: int):
        self._call(Cmd.GET_DATA, Data.ADC_READ.value, id)
        # Now this is screwy.
        # DATA0 gets set to 0 or 1, indicating the voldage type
        # DATA1 and DATA2 are a 16bi number that need to be reassembled.
        # Note that DATA2 is the high bits.

        val = self._read(Reg.DATA2) << 8 + self._read(Reg.DATA1)
        type = self._read(Reg.DATA0)

        if type == 0:
            # Voltage type '1' 3v3 REF, Voltage /2
            val *= 6.4453125
        elif type == 1:
            # Voltage type '2' 3v3 REF, Voltage = ((VIN*1.07)/10+1.07)
            val *= 33.34093896028037
        else:
            raise ValueError("Unknown voltage type %d" % type)

        return val

    def read_temp(self) -> int:
        # Now this is screwy.
        # DATA0 is ... something expected to be 2
        # DATA1 and DATA2 form a low/high 16bi number. Unit is Kelvin.
        if self._call(Cmd.GET_DATA, Data.ADC_TEMP.value) == 2:
            return self._read(Reg.DATA2) << 8 + self._read(Reg.DATA1)


class ClusterHATDriver(ClusterCTRLDriver):
    """The ClusterHAT controller supports some verbs not supported by the basic ClusterCTRL board."""

    # FIXME: The ClusterHAT also has some CONSIDERABLE differences in how it does I/O, due to leveraging RPi GPIO not
    # just i2c. Whether this is essential or incidental is unclear.

    def led_on(self, id: int):
        """Turn on an LED by ID."""

        assert self.type is BoardType.PHAT
        return self._call(Cmd.LED_EN, id)

    def led_off(self, id: int):
        """Turn off an LED by ID."""

        assert self.type is BoardType.PHAT
        return self._call(Cmd.LED_DIS, id)
