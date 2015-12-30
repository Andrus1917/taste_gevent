# Попытка использования 'gevent' для передачи файлов по самопальному протоколу

Не стал создавать requirements.txt

## Необходимые приложения:
* Twisted==15.5.0
* argparse==1.2.1
* gevent==1.0.2
* greenlet==0.4.9
* wsgiref==0.1.2
* zope.interface==4.1.3

## Данные
Два подкаталога:
* _files - где лежат исходные файлы;
* _data - куда пишутся принятые сервисом файлы.


## Запуск сервиса:

```
./run_server.py 
```
## Запуск клиента (без пропатченных сокетов):

```
 ./client.py
```

## Запуск клиента (с пропатченными сокетами):

```
./client.py --use-gevent-sockets
```
