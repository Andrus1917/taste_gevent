#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Тестовый сервер.
"""

import os
import sys

sys.path += ['.', '..']

import signal

from twisted.internet.protocol import Factory
from twisted.internet import reactor
from twisted.python import log

from protocol import TestedProtocol


DEFAULT_PORT = 8600


def main():

    factory = Factory()
    factory.protocol = TestedProtocol
    reactor.listenTCP(DEFAULT_PORT, factory)
    reactor.run()


if __name__ == '__main__':
    main()
