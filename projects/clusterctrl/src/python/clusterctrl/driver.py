"""An I2C driver for the ClusterCTRL/ClusterHAT family of device(s)."""

from enum import Enum
from itertools import chain, repeat
import logging
from random import SystemRandom
from time import sleep
from typing import NamedTuple, Union


log = logging.getLogger(__name__)

# Variable source import "smbus"
#  - smbus can come from i2c-dev (host package, c ext.)
#  - smbus2 is a PyPi hosted pure Python implementation
#
# In order to support reasonable packaging and deployment, we want to prefer
# smbus and fall back to smbus2 if it isn't available.
smbus = None

if not smbus:
    try:
        import smbus
    except ImportError as e:
        log.warning(e)

if not smbus:
    try:
        import smbus2 as smbus
    except ImportError as e:
        log.warning(e)

if not smbus:
    raise ImportError("Unable to load either SMBus or SMBus2")


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
    SINGLE = 0x01  # Do the 'single' and 'triple' really use the same board ID?
    TRIPLE = 0x01  # ???
    PHAT = 0x02    # The ClusterHAT boards
    CTRL = 0x02    # The ClusterCTRL boards
    A6 = 0x03      # https://clusterctrl.com/p/aplus6
    STACK = 0x04   # https://shop.pimoroni.com/products/clusterctrl-stack


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
    SAVE_DEFAULTS = 0xF1  # Save factory defaults
    GET_DATA = 0xF2  # Get DATA (Temps/ADC/etc.)
    SAVE_ORDER = 0xF3  # Save order to EEPROM
    SAVE_USBBOOT = 0xF4  # Save usbboot status to EEPROM
    SAVE_POS = 0xF5  # Save Power On State to EEPROM
    SAVE_LEDS = 0xF6  # Save LED to EEPROM
    NOP = 0x90  # Do nothing


class Data(Enum):
    """Datum that can be read back from the Cluster device via Cmd.GET_DATA"""

    # Get arbitrary data from ClusterCTRL
    VERSION = 0x00  # Get firmware version
    ADC_CNT = 0x01  # Returns number of ADC ClusterCTRL supports
    ADC_READ = 0x02  # Read ADC data for ADC number 'data0'
    ADC_TEMP = 0x03  # Read Temperature ADC
    FANSTATUS = 0x04  # Read fan status


class PiRef(NamedTuple):
    """An ID for a specific Pi/PiZero controlled by a Cluster{CTRL,HAT}.

    These IDs are expected to be unique at the host level; not at the cluster level.

    """
    controller_id: int
    pi_id: int

    def __repr__(self) -> str:
        return f"<PiRef {self.controller_id:d}-{self.pi_id:d}>"


class ClusterCTRLv2Driver(object):
    def __init__(self,
                 bus: smbus.SMBus,
                 address: int = I2C_ADDRESS,
                 delay: int = 0,
                 clear: bool = False):
        """Initialize a ClusterCTRL/ClusterHAT driver instance for a given bus device."""
        self._bus = bus
        self._address = address
        self._delay = delay
        self._clear = clear

        try:
            if (version := self._read(Reg.VERSION)) != 2:
                raise IOError(f"Unsupported register format {version}; expected 2")
        except:
            raise ValueError("Cannot communicate with a ClusterCTRL/ClusterHAT on the given bus")

        self._post_init()

    def _post_init(self):
        # This is a firmware default value indicating an uninitialized board.
        # Randomize it if present and the user hasn't told us not to.
        if self.get_order() == 20:
            v = 20
            r = SystemRandom()
            while v == 20:
                v = r.randint(0, 256)
            self.set_order(v)
            self.eeprom_save_order()

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

    @staticmethod
    def _repack(values):
        """Pack an array of bytes back into a single value."""
        acc = 0
        for b in values:
            acc = acc << 8
            acc += b
        return acc

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

    def _id(self, id: Union[PiRef, int]) -> int:
        """Validate a user-provided ID and convert it to a numeric one."""

        if isinstance(id, PiRef):
            # Yes this is backwards, but its' most convenient for sharing validation
            assert self.get_order() == id.controller_id
            id = id.pi_id
        elif isinstance(id, int):
            pass
        else:
            raise ValueError(f"Expected an int or PiRef, got {type(id)}")

        maxpi = self._read(Reg.MAXPI)
        if 0 <= id <= maxpi:
           return id
        else:
            raise ValueError("Expected an id in [0,{maxpi:d}], got {id:d}")

    def min_pi(self):
        """Get the minimum supported Pi ID on this controller."""

        return PiRef(self.get_order(), 1)

    @once
    def max_pi(self):
        """Get the maximum supported Pi ID on this controller."""

        return PiRef(self.get_order(), self._read(Reg.MAXPI))

    def pis(self):
        """Iterate over the IDs of Pis which could be connected to this controller."""

        order = self.get_order()
        maxpi = self._read(Reg.MAXPI)
        for i in range(1, maxpi + 1):
            yield PiRef(order, i)

    @property
    def type(self) -> BoardType:
        return BoardType(self._read(Reg.TYPE))

    @property
    def fw_version(self):
        self._read(Data.VERSION)
        return (self._read(Reg.DATA1), self._read(Reg.DATA0))

    def reset_all(self):
        """[Power] cycle the entire Controller."""

        try:
            return self._call(Cmd.RESET)
        except OSError:
            # An OSError I/O to the reset board is somewhat expected
            pass

    ####################################################################################################
    # EEPROM management
    ####################################################################################################
    def eeprom_save_all(self):
        """Persist all supported options to EEPROM."""

        return self._call(Cmd.SAVE)

    def eeprom_reset(self):
        """Reset EEPROM to factory/firmware default value(s)."""

        return self._call(Cmd.SAVE_DEFAULTS)

    def eeprom_save_powerstate(self):
        """Persist the current power state to EEPROM."""

        return self._call(Cmd.SAVE_POS)

    def eeprom_save_leds(self):
        """Persist the current LED state to EEPROM."""

        return self._call(Cmd.SAVE_LEDS)

    def eeprom_save_order(self):
        """Persist the current order value to EEPROM."""

        return self._call(Cmd.SAVE_ORDER)

    def eeprom_save_usbboot(self):
        """Persist USB booting settings to EEPROM."""

        return self._call(Cmd.SAVE_USBBOOT)

    ####################################################################################################
    # USB hub management
    ####################################################################################################
    def hub_on(self):
        """Turn on the USB hub."""

        return self._call(Cmd.HUB_ON)

    def hub_off(self):
        """Turn off the USB hub."""

        return self._call(Cmd.HUB_OFF)

    # FIXME: Is hub_status unsupported in the firmware?

    def hub_reset(self, delay: int = 0):
        """[Power] cycle the Controller hub for `delay` x 10ms."""

        return self._call(Cmd.HUB_CYCLE, delay)

    ####################################################################################################
    # Power management
    ####################################################################################################
    def power_on(self, id: Union[PiRef, int]):
        """Power on a given slot by ID."""

        id = self._id(id)
        return self._call(Cmd.ON, id)

    def power_off(self, id: Union[PiRef, int]):
        """Power off a given slot by ID."""

        id = self._id(id)
        return self._call(Cmd.OFF, id)

    def power_status(self, id: Union[PiRef, int]):
        """Read the status of a given slot by ID."""

        id = self._id(id)
        return self._call(Cmd.GET_PSTATUS, id)

    def power_all_on(self):
        """Power on all slots in this Controller."""

        for id in self.pis():
            self.power_on(id)

    def power_all_off(self):
        """Power off all slots in this Controller."""

        for id in self.pis():
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

        assert 0 < order <= 255, "Order must be in the single byte range"
        assert order != 20, "20 is the uninitialized order value, use something else"
        return self._call(Cmd.SET_ORDER, order)

    ####################################################################################################
    # USB booting
    ####################################################################################################
    def usbboot_on(self, id: Union[PiRef, int]):
        """Enable USB booting for the given Pi."""

        id = self._id(id)
        return self._call(Cmd.USBBOOT_EN, id)

    def usbboot_off(self, id: Union[PiRef, int]):
        """Disable USB booting for the given Pi."""

        id = self._id(id)
        return self._call(Cmd.USBBOOT_DIS, id)

    def usbboot_status(self, id: Union[PiRef, int]):
        """Get the current USB booting status for the given Pi."""

        id = self._id(id)
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

    def read_adc(self, adc_id: int):
        self._call(Cmd.GET_DATA, Data.ADC_READ.value, adc_id)
        # Now this is screwy.
        # DATA0 gets set to 0 or 1, indicating the voldage type
        # DATA1 and DATA2 are a 16bi number that need to be reassembled.
        # Note that DATA2 is the high bits.

        val = self._repack(self._read(Reg.DATA2, 2))
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
            return self._repack(self._read(Reg.DATA2, 2))

    ####################################################################################################
    # Operations with inconsistent platform support
    ####################################################################################################
    def led_on(self, id: Union[PiRef, int]):
        """Turn on an LED by ID."""

        id = self._id(id)
        return self._call(Cmd.LED_EN, id)

    def led_off(self, id: Union[PiRef, int]):
        """Turn off an LED by ID."""

        id = self._id(id)
        return self._call(Cmd.LED_DIS, id)

    # FIXME: LED status?
