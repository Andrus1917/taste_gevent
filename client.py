#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import socket
import time
import argparse

import gevent

class ProtocolError(Exception):
    pass

PREPARE_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname( __file__), '_files/'))

BUFFER_SIZE = 4096
EXPECTED_CODES = [220, 230, 250]


def parse_line(line):
    parts = line.strip().split(None, 1)
    if not parts or len(parts) < 2:
        raise ProtocolError(u'The invalid message format: <%s> ' % line)
    try:
        code = int(parts[0])
    except TypeError:
        raise ProtocolError(u'The invalid code: <%s>' % parts[0])
    else:
        msg = parts[0]
        return (code, msg)


def send_line(s, msg):
    s.send('%s\r\n' % msg)


def send_to(file_path, num):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    try:
        s.connect(('localhost', 8600))
    except socket.error:
        raise RuntimeError, u'No connection to Tested server'

    resp = s.recv(BUFFER_SIZE)
    (code, msg) = parse_line(resp)
    exp_code = EXPECTED_CODES[0]
    if code != exp_code:
        raise ProtocolError(u'The invalid expected code: <%d> != <%d>' % \
            (code, exp_code))

    send_line(s, 'PUT %s' % file)
    resp = s.recv(BUFFER_SIZE)
    (code, msg) = parse_line(resp)
    exp_code = EXPECTED_CODES[1]
    if code != exp_code:
        raise ProtocolError(u'The invalid expected code: <%d> != <%d>' % \
            (code, exp_code))

    file_name = file_path.split('/')[-1]
    send_line(s, 'Content-type: binary')
    send_line(s, 'Length: %d' % os.path.getsize(file_path))
    send_line(s, 'Filename: %s' % file_name)
    send_line(s, '')

    i = 0
    with open(file_path, 'r') as fp:
        while True:
            data = fp.read(BUFFER_SIZE)
            if not data:
                break
            s.sendall(data)
            i += 1

    s.send('\r\n')

    while True:
        resp = s.recv(BUFFER_SIZE)
        try:
            (code, msg) = parse_line(resp)
            break
        except:
            pass

    exp_code = EXPECTED_CODES[2]
    if code != exp_code:
        raise ProtocolError(u'The invalid expected code: <%d> != <%d>' % \
            (code, exp_code))
    s.close()
    return True


def test_gevent(i, file_path):
    """
    Посылает файл на сервер.
    """
    send_to(file_path, i)
    print(u'Задание %s завершено' % i)


def get_files(folder=PREPARE_FOLDER):
    """
    Генератор списка файлов.
    """
    task_no = 1
    for file_name in os.listdir(PREPARE_FOLDER):
        file_path = os.path.join(PREPARE_FOLDER, file_name)
        if os.path.exists(file_path):
            yield (task_no, file_path)
            task_no += 1



def main(use_gevent_sockets=False):
    """
    Основная функция.

    Проходит во всем файлам в указанном каталоге и отсылает их на сервер.
    """
    if use_gevent_sockets:
        from gevent import monkey; monkey.patch_all()

    gevent.joinall([gevent.spawn(test_gevent, task_no, file_path) \
        for task_no, file_path in get_files()])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'Тестирование')
    parser.add_argument('--use-gevent-sockets', action='store_true',
                        default=False)
    args = parser.parse_args()
    main(use_gevent_sockets=args.use_gevent_sockets)
