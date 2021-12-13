"""An implementation of ring buffers which supports efficient reverse scans."""

class Ringbuffer(object):
    def __init__(self, size: int, seed: list = None, fill: object = None):
        if seed:
            assert len(seed) <= size
        self._state = ((seed or []) + [fill] * size)[:size]
        self._size = size
        self._start = 0
        self._end = len(seed) if seed else 0

    def append(self, obj):
        self._state[self._end % self._size] = obj
        self._end = (self._end + 1) % self._size
        self._start = (self._start + 1) % self._size

    def __iter__(self):
        if self._start < self._end:
            yield from iter(self._state[self._start:self._end])
        else:
            yield from iter(self._state[self._start:] + self._state[:self._end])

    def __reversed__(self):
