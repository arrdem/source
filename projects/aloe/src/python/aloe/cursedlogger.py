import logging
import curses

from collections import deque as ringbuffer
from itertools import count


class CursesHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self._screen = screen
        self._buff = ringbuffer(maxlen=screen.getmaxyx()[0] - 2)

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"
            self._buff.append(msg)
            self._screen.clear()
            for i, msg in zip(count(1), self._buff):
                self._screen.addstr(i, 2, msg)
            self._screen.border()
            self._screen.refresh()

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
