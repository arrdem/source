"""A quick and dirty octoprint status screen"""

from configparser import ConfigParser
import curses
from datetime import timedelta
from itertools import count
import os
import signal
from time import sleep

from octorest.client import OctoRest
import yaml


def draw(screen, client):
    """Poll the client for a status, draw it to the screen."""

    # Screen details
    rows, cols = screen.getmaxyx()

    # Poll the API

    try:
        job = client.job_info()
        # >>> client.job_info()
        # {'job': {'averagePrintTime': 7965.021392323004,
        #          'estimatedPrintTime': 6132.310772608108,
        #          'filament': {'tool0': {'length': 8504.781600002587,
        #                                 'volume': 20.456397036761484}},
        #          'file': {'date': 1638666604,
        #                   'display': 'v2-sides.gcode',
        #                   'name': 'v2-sides.gcode',
        #                   'origin': 'local',
        #                   'path': 'v2-sides.gcode',
        #                   'size': 1074906},
        #          'lastPrintTime': 7965.021392323004,
        #          'user': '_api'},
        #  'progress': {'completion': 100.0,
        #               'filepos': 1074906,
        #               'printTime': 7965,
        #               'printTimeLeft': 0,
        #               'printTimeLeftOrigin': None},
        #  'state': 'Operational'}

        printer = client.printer()
        # >>> client.printer()
        # {'sd': {'ready': False},
        #  'state': {'error': '',
        #            'flags': {'cancelling': False,
        #                      'closedOrError': False,
        #                      'error': False,
        #                      'finishing': False,
        #                      'operational': True,
        #                      'paused': False,
        #                      'pausing': False,
        #                      'printing': False,
        #                      'ready': True,
        #                      'resuming': False,
        #                      'sdReady': False},
        #            'text': 'Operational'},
        #  'temperature': {'bed': {'actual': 23.05, 'offset': 0, 'target': 0.0},
        #                  'tool0': {'actual': 23.71, 'offset': 0, 'target': 0.0}}}

        # Draw a screen

        flags = printer["state"]["flags"]
        ready = not flags["error"] and flags["operational"] and flags["ready"]
        printing = flags["printing"]

        file = job["job"]["file"]
        progress = job["progress"]
        completion = progress["completion"] / 100.0
        time_remaining = timedelta(seconds=progress["printTimeLeft"])

        progress_cols = int(cols * completion)
        progress_line = ("#" * progress_cols) + ("-" * (cols - progress_cols))

        screen.addstr(0, 0, f"Ready: {ready}")
        if printing:
            screen.addstr(2, 0, f"Printing: {file['name']}")
            screen.addstr(3, 0, f"Remaining print time: {time_remaining}")

        screen.addstr(5, 0, progress_line)

        for i, l in zip(count(7), yaml.dump({"job": job, "printer": printer}).splitlines()):
            if i >= rows:
                break
            else:
                screen.addstr(i, 0, l)

    except Exception as e:
        screen.addstr(str(e))


if __name__ == "__main__":
    config = ConfigParser()
    config.read(os.path.expanduser("~/.config/octoprint-cli.ini"))

    client = OctoRest(url="http://" + config["server"]["ServerAddress"],
                      apikey=config["server"]["ApiKey"])

    screen = curses.initscr()

    # Remap a SIGTERM to a kbd int so a clean shutdown is easy
    def kbdint(*args):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, kbdint)

    try:
        while True:
            try:
                screen.clear()
                draw(screen, client)
                screen.refresh()
                sleep(1)
            except KeyboardInterrupt:
                break

    finally:
        curses.endwin()
