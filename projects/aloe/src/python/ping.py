"""A shitty ping wrapper."""


from datetime import timedelta
from subprocess import check_call, DEVNULL


def ping(host: str,
         count: int = 3,
         interval: float = 0.3,
         timeout: timedelta = timedelta(seconds=3)):
    return check_call(["ping", "-q",
                       "-i", str(interval),
                       "-c", str(count),
                       "-W", str(timeout.total_seconds()),
                       host],
                      stdout=DEVNULL,
                      stderr=DEVNULL,)
