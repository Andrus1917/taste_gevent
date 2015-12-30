# -*- encoding: utf-8 -*-

"""
Простой протокол джля теста
"""

import os
import socket
import uuid
import time

from twisted.protocols import basic, policies
from twisted.python.runtime import platform

DATA_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname( __file__), '_data/'))

# Ошибки
BAD_COMMAND_CODE = 500
DEFAULT_BAD_COMMAND_MSG = u"""Неверный синтаксис команды"""

if platform.isMacOSX():
    DNSNAME = socket.gethostname()
else:
    DNSNAME = socket.getfqdn()


class ProtocolError(Exception):
    """
    Исключение для некорректных команд.
    """


class TestedProtocol(basic.LineReceiver, policies.TimeoutMixin):
    """
    Тестовый протокол.
    """

    timeout = 600
    host = DNSNAME
    guest_host = None

    # Ждем команды от клиента
    wait_command = True

    # Спсиок разрешенных команд
    COMMANDS = ['PUT',]

    def __init__(self, *args, **kwargs):
        self._headers = []
        self._filename = None
        self._fp = None

    def greeting(self):
        return u'Проверка тестового протокола, хост <%s>' % self.host

    def connectionMade(self):
        """
        Соединение установлено.
        """
        peer = self.transport.getPeer()
        try:
            self.guest_host = peer.host
        except AttributeError:
            self.guest_host = str(peer)
        self.sendCode(220, self.greeting())
        self.setTimeout(self.timeout)

    def sendLine(self, line):
        """
        Посылка строки в текстовом режиме.
        """
        self.transport.write(str(line) + '\r\n')

    def lineReceived(self, line):
        """
        Получение данных в текстовом режиме.
        """

        self.resetTimeout()
        if self.wait_command:
            self.parseCommand(line)
        elif line == b'':
            # Завершаем текстовый режим
            if self._headers and 'FILENAME' in dict(self._headers):
                self._filename = os.path.join(DATA_FOLDER,
                    dict(self._headers).get('FILENAME'))
                try:
                    self._fp = open(self._filename, 'w')
                except IOError:
                    raise RuntimeError(u'Ошибка открытия файла')
            else:
                self.fp = tempfile.NamedTemporaryFile(dir=DATA_FOLDER)
            self.setRawMode()
        else:
            self.parseHeader(line)


    def rawDataReceived(self, data):
        """
        Получение данных в нетекстовом режиме.
        """
        self.resetTimeout()

        is_finish = False
        if data.endswith('\r\n'):
            is_finish = True
            data = data[:-2]

        self._fp.write(data)
        if is_finish:
            self._fp.close()
            self.sendCode(250, 'Data recieved')
            self.setLineMode()
            self.wait_command = True

    def sendCode(self, code, message=''):
        lines = ' ' . join([l.strip() for l in message.splitlines()])
        self.sendLine('%3.3d %s' % (code, lines or ''))

    def sendError(self, code, error_msg):
        self.sendCode(code, error_msg)

    def setCommand(self, command_name):
        if command_name in self.COMMANDS:
            self.command = command_name
        else:
            self.wait_command = True
            self.command = None
            self.args = None
            raise ProtocolError(u'The invalid command: <%s>' % command_name)

    def setArgs(self, args):
        self.args = args

    def parseCommand(self, line):
        """Parse the command line.

        Ignore leading and trailing spaces.
        """
        parts = line.strip().split(None, 1)
        try:
            if not parts or len(parts) < 2:
                raise ProtocolError(DEFAULT_BAD_COMMAND_MSG)
            self.setCommand(parts[0].strip().upper())
            self.setArgs(parts[1])
        except SyntaxError as exc:
            self.sendError(500, 'ERROR: %s' % str(exc))
        else:
            self.wait_command = False
            self.sendCode(230, 'OK, Waiting for a data')

    def parseHeader(self, line):

        parts = line.strip().split(':', 1)
        if not parts or len(parts) < 2:
            self.sendCode(510, 'The invalid format for the header')
        else:
            k, v = map(lambda x: x.strip(), parts[:2])
            self._headers.append((k.upper(), v))

