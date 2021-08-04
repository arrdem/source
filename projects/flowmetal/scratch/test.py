#!astinterp

from __future__ import print_function


class Foo(object):
    def bar(self):
        return 1

    @property
    def baz(self):
        print("'Computing' baz...")
        return 2


a = Foo()
print(a.bar())
print(a.baz)

import random


for _ in range(10):
    print(random.randint(0, 1024))


def bar(a, b, **bs):
    pass

import requests


print(len(requests.get("https://pypi.org/pypi/requests/json").text))
