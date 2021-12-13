"""Aloe - A shitty weathermapping tool.

Think MTR but with the ability to detect/declare incidents and emit logs.

Periodically traceroutes the egress network, and then walks pings out the egress network recording times and hosts which
failed to respond. Expects a network in excess of 90% packet delivery, but with variable timings. Intended to probe for
when packet delivery latencies radically degrade and maintain a report file.

"""

import argparse
from collections import deque as ringbuffer
import curses
from datetime import timedelta
from itertools import count
import logging
import queue
from queue import Queue
import sys
from threading import Event, Lock, Thread
from time import sleep, time

from .icmp import *
from .icmp import _ping
from .cursedlogger import CursesHandler

import pytz


log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("hosts", nargs="+")

INTERVAL = 0.5

Z = pytz.timezone("America/Denver")


class HostState(object):
    """A model of a (bounded) time series of host state.

    """


class MonitoredHost(object):
    def __init__(self, hostname: str, timeout: timedelta, id=None):
        self._hostname = hostname
        self._timeout = timeout
        self._sequence = request_sequence(hostname, timeout, id)
        self._lock = Lock()
        self._state = ringbuffer(maxlen=360)
        self._is_up = False
        self._lost = 0
        self._up = 0

    def __call__(self, shutdown: Event, q: Queue):
        """Monitor a given host by throwing requests into the queue; intended to be a Thread target."""

        while not shutdown.is_set():
            req = next(self._sequence)
            resp = _ping(q, req)

            if resp and not self._is_up:
                # log.debug(f"Host {self._hostname} is up!")
                self._is_up = self._is_up or resp
                self._up = resp._time

            elif resp and self._is_up:
                # log.debug(f"Host {self._hostname} holding up...")
                pass

            elif not resp and self._is_up:
                # log.debug(f"Host {self._hostname} is down!")
                self._is_up = None
                self._up = None

            elif not resp and not self._is_up:
                pass

            with self._lock:
                if not resp:
                    self._lost += 1
                if self._state and not self._state[0]:
                    self._lost -= 1

                # self._state = (self._state + [req])[:-3600]
                self._state.append(resp)

            sleep(1)

    def last(self):
        with self._lock:
            return next(reversed(self._state), None)

    def last_window(self, duration: timedelta = None):
        with self._lock:
            l = []
            t = time() - duration.total_seconds()
            for i in reversed(self._state):
                if not i or i._time > t:
                    l.insert(0, i)
                else:
                    break
            return l

    def loss(self, duration: timedelta):
        log = self.last_window(duration)
        if log:
            return log.count(None) / len(log)
        else:
            return 0.0

    def is_up(self, duration: timedelta, threshold = 0.25):
        return self.loss(duration) <= threshold

    def last_seen(self, now: datetime) -> timedelta:
        if state := self.last():
            return now - datetime.fromtimestamp(state._time)

    def up(self, duration: datetime):
        if self._up:
            return datetime.fromtimestamp(self._up)


def main():
    stdscr = curses.initscr()
    maxy, maxx = stdscr.getmaxyx()

    begin_x = 2; begin_y = maxy - 12
    height = 10; width = maxx - 4
    logscr = curses.newwin(height, width, begin_y, begin_x)

    handler = CursesHandler(logscr)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    stdscr = curses.newwin(maxy - height - 2, width, 0, begin_x)

    opts, args = parser.parse_known_args()

    q = queue.Queue()
    shutdown = Event()

    p = Thread(target=icmp_worker, args=(shutdown, q,))
    p.start()

    hosts = {}
    hl = Lock()
    threads = {}

    def create_host(address):
        if address not in hosts:
            log.info(f"Monitoring {address}...")
            with hl:
                hosts[address] = monitor = MonitoredHost(address, timedelta(seconds=8))
                threads[address] = t = Thread(target=monitor, args=(shutdown, q))
            t.start()

        else:
            log.debug(f"Already monitoring {address}...")

        stdscr.refresh()

    def render():
        dt = timedelta(seconds=8)

        with open("incidents.txt", "w") as fp:
            incident = False
            while not shutdown.is_set():
                rows, cols = stdscr.getmaxyx()
                down = 0
                now = datetime.now()
                i = 0
                with hl:
                    for host, i in zip(hosts.values(), count(1)):
                        name = host._hostname
                        loss = host.loss(dt) * 100
                        state = host.last()
                        if not state:
                            down += 1
                            last_seen = "Down"
                        else:
                            last_seen = f"{host.last_seen(now).total_seconds():.2f}s ago"

                        if up := host.up(dt):
                            up = f" up: {(now - up).total_seconds():.2f}"
                        else:
                            up = ""

                        stdscr.addstr(i, 2, f"{name: <16s}]{up} lost: {loss:.2f}% last: {last_seen}".ljust(cols))

                stdscr.border()
                stdscr.refresh()

                msg = None
                if down >= 3 and not incident:
                    incident = True
                    msg = f"{datetime.now()} - {down} hosts down"

                elif down < 3 and incident:
                    incident = False
                    msg = f"{datetime.now()} - network recovered"

                if i != 0 and msg:
                    log.info(msg)
                    fp.write(msg + "\n")
                    fp.flush()

                sleep(1)

    rt = Thread(target=render)
    rt.start()

    def retrace():
        while not shutdown.is_set():
            for h in opts.hosts:
                # FIXME: Use a real topology model
                for hop in traceroute(q, h):
                    if ping(q, hop.address).is_alive:
                        create_host(hop.address)

            sleep(60 * 5)

    tt = Thread(target=retrace)
    tt.start()

    try:
        while True:
            sleep(1)
    finally:
        curses.endwin()
        sys.stdout.flush()
        sys.stderr.flush()
        shutdown.set()


if __name__ == "__main__":
    main()
