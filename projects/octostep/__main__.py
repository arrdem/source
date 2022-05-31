"""A quick and dirty octoprint status screen"""

from configparser import ConfigParser
import os

from octorest.client import OctoRest


if __name__ == "__main__":
    config = ConfigParser()
    config.read(os.path.expanduser("~/.config/octoprint-cli.ini"))

    client = OctoRest(url="http://" + config["server"]["ServerAddress"],
                      apikey=config["server"]["ApiKey"])

    for line in open(sys.argv[1], "r"):
        l = line.split(";")[0]
        l = l.strip()
        if not l:
            continue

        while True:
            print(f"\n> {l}")
            cmd = input("[seq?] >>> ")
            if cmd == "s":
                client.gcode(l)
                break
            elif cmd == "e":
                client.gcode("M112")
            elif cmd == "q":
                exit(0)
            elif cmd == "n":
                break
            elif cmd == "?":
                print("""\
s[tep]  - run the next g-code line in the file
n[ext]  - skip this line
e[stop] - issue an emergency stop
q[uit]  - exit the debugger""")

            else:
                client.gcode(line)
