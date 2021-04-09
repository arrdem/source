"""
Bits and bats.

Mainly bats.
"""

import re


def memoize(f):
    memo = {}

    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]

    return helper


@memoize
def re_mem(regex):
    return re.compile(regex)
