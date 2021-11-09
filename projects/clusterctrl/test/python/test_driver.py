"""Tests covering the v2 ClusterCTRL driver."""

from clusterctrl.driver import (
    BoardType,
    ClusterCTRLv2Driver,
    Cmd,
    Data,
    Reg,
)
import pytest


class MockSMBus(object):
    """An object that looks like smbus[2].SMBus.

    This object builds an append/mock log of all i2c calls performed, allowing a
    user to assert that a specific sequence of reads and writes was issued.

    """

    def __init__(self, regs={}):
        self._log = []
        self._regs = regs
        self._retvals = []

    def read_byte_data(self, bus_addr, memory_addr) -> int:
        self._log.append(["read", bus_addr, memory_addr])
        return self._regs[memory_addr]

    def write_byte_data(self, bus_addr, memory_addr, value) -> None:
        self._regs[memory_addr] = value
        self._log.append(["write", bus_addr, memory_addr, value])

        # Minimum viable call/return mocking
        if memory_addr == Reg.CMD.value:
            # Clear data registers after a "call"
            for r in range(Reg.DATA7.value, Reg.CMD.value):
                self._regs[r] = 0

            if self._retvals:
                self._regs[Reg.DATA0.value] = self._retvals.pop()

    def read_block_data(self, bus_addr, memory_addr, block_size) -> int:
        raise NotImplemented


@pytest.fixture
def bus():
    """An SMBus-alike object."""

    regs = {x: 0 for x in range(0, 16)}
    regs[Reg.ORDER.value] = 13  # (un)lucky 13
    regs[Reg.VERSION.value] = 2
    regs[Reg.MAXPI.value] = 5
    return MockSMBus(regs)


@pytest.fixture
def driver(bus):
    """The driver under test atop a mocked bus."""

    driver = ClusterCTRLv2Driver(bus)
    bus._log.clear()  # The driver has startup behavior, so flush the log
    return driver


def sublist(l1, l2):
    """Naive but adequate sublist testing."""

    for i in range(len(l1)):
        if l1[i] == l2[0]:
            for j in range(len(l2)):
                try:
                    if l1[i + j] != l2[j]:
                        break
                except IndexError:
                    break
            else:
                return True
    return False


def assert_log(bus, log):
    def simplify(e):
        if hasattr(e, "value"):
            return e.value
        else:
            return e

    log = [[simplify(e) for e in cmd] for cmd in log]

    assert sublist(bus._log, log), "\n".join(
        ["Failed to find expected sublog", "log:"]
        + [f"- {e}" for e in bus._log]
        + ["expected:"]
        + [f"- {e}" for e in log]
    )


def test_get_order(bus, driver):
    """Check that get_order sends the appropriate command sequence."""

    assert driver.get_order() == 13
    assert_log(bus, [["read", 0x20, Reg.ORDER]])


def test_set_order(bus, driver):
    """Check that set_order sends the appropriate command sequence."""

    driver.set_order(14)
    assert_log(
        bus, [["write", 0x20, Reg.DATA0, 14], ["write", 0x20, Reg.CMD, Cmd.SET_ORDER]]
    )


def test_type(bus, driver):
    assert isinstance(driver.type, BoardType)
    assert_log(bus, [["read", 0x20, Reg.TYPE]])


def test_version(bus, driver):
    assert driver.fw_version
    # Invoke "read version"
    assert_log(
        bus,
        [
            ["write", 0x20, Reg.DATA0, Data.VERSION],
            ["write", 0x20, Reg.CMD, Cmd.GET_DATA],
        ],
    )
    # Read the two relevant registers
    assert_log(bus, [["read", 0x20, Reg.DATA1], ["read", 0x20, Reg.DATA0]])


def test_reset(bus, driver):
    driver.reset_all()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.RESET]])


def test_eeprom_save_all(bus, driver):
    driver.eeprom_save_all()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE]])


def test_eeprom_reset(bus, driver):
    driver.eeprom_reset()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE_DEFAULTS]])


def test_eeprom_save_powerstate(bus, driver):
    driver.eeprom_save_powerstate()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE_POS]])


def test_eeprom_save_leds(bus, driver):
    driver.eeprom_save_leds()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE_LEDS]])


def test_eeprom_save_order(bus, driver):
    driver.eeprom_save_order()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE_ORDER]])


def test_eeprom_save_ussbboot(bus, driver):
    driver.eeprom_save_usbboot()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.SAVE_USBBOOT]])


def test_hub_on(bus, driver):
    driver.hub_on()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.HUB_ON]])


def test_hub_off(bus, driver):
    driver.hub_off()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.HUB_OFF]])


def test_hub_reset(bus, driver):
    driver.hub_reset()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.HUB_CYCLE]])


def test_power_status(bus, driver):
    bus._retvals.append(1)  # Set a mocked return code.
    assert driver.power_status(1) == 1
    assert_log(
        bus, [["write", 0x20, Reg.DATA0, 1], ["write", 0x20, Reg.CMD, Cmd.GET_PSTATUS]]
    )


def test_pis(bus, driver):
    assert len(list(driver.pis())) == 5


def test_power_all_on(bus, driver):
    driver.power_all_on()

    for pi in driver.pis():
        assert_log(
            bus,
            [["write", 0x20, Reg.DATA0, pi.pi_id], ["write", 0x20, Reg.CMD, Cmd.ON]],
        )


def test_power_all_off(bus, driver):
    driver.power_all_off()

    for pi in driver.pis():
        assert_log(
            bus,
            [["write", 0x20, Reg.DATA0, pi.pi_id], ["write", 0x20, Reg.CMD, Cmd.OFF]],
        )


def test_alert_on(bus, driver):
    driver.alert_on()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.ALERT_ON]])


def test_alert_off(bus, driver):
    driver.alert_off()
    assert_log(bus, [["write", 0x20, Reg.CMD, Cmd.ALERT_OFF]])


def test_fan_on(bus, driver):
    driver.fan_on()
    assert_log(bus, [["write", 0x20, Reg.DATA0, 1], ["write", 0x20, Reg.CMD, Cmd.FAN]])


def test_fan_off(bus, driver):
    driver.fan_off()
    assert_log(bus, [["write", 0x20, Reg.DATA0, 0], ["write", 0x20, Reg.CMD, Cmd.FAN]])


def test_fan_status(bus, driver):
    driver.fan_status()
    assert_log(
        bus,
        [
            ["write", 0x20, Reg.DATA0, Data.FANSTATUS],
            ["write", 0x20, Reg.CMD, Cmd.GET_DATA],
        ],
    )


def test_get_order(bus, driver):
    driver.get_order()
    assert_log(bus, [["read", 0x20, Reg.ORDER]])


def test_set_order(bus, driver):
    driver.set_order(253)
    assert_log(
        bus, [["write", 0x20, Reg.DATA0, 253], ["write", 0x20, Reg.CMD, Cmd.SET_ORDER]]
    )
