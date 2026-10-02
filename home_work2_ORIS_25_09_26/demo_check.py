import contextlib
import io
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import protocol as proto
import server


def show(sock, expected, contains=''):
    command, payload = proto.recv_message(sock)
    text = payload.decode('utf-8')
    assert command == expected, (command, expected)
    assert contains in text, (contains, text)
    print(f'Получено {command}: {text}')
    return text


def connect(name):
    sock = socket.create_connection(('127.0.0.1', port), timeout=3)
    proto.send_message(sock, 'JOIN', name.encode('utf-8'))
    show(sock, 'TEXT', name)
    return sock


listener = socket.socket()
listener.bind(('127.0.0.1', 0))
listener.listen()
port = listener.getsockname()[1]


def accept_clients():
    while True:
        try:
            sock, addr = listener.accept()
        except OSError:
            return
        threading.Thread(target=server.handle_client, args=(sock, addr), daemon=True).start()


threading.Thread(target=accept_clients, daemon=True).start()
print('1. Протокол и старые команды (настоящие TCP-соединения)')
a = connect('Аня')
b = connect('Боря')
show(a, 'TEXT', 'присоединился')
proto.send_message(a, 'TEXT', 'Привет!'.encode('utf-8'))
show(b, 'TEXT', 'Аня: Привет!')
proto.send_message(a, 'LIST')
show(a, 'LIST', 'Боря')
proto.send_message(a, 'UNKNOWN')
show(a, 'ERROR', 'unknown command')
print('ERROR получен целиком: 5 символов.')

print('\n3. Смена имени без переподключения')
proto.send_message(a, 'NICK', 'Катя'.encode('utf-8'))
show(a, 'TEXT', 'Аня теперь известен как Катя')
show(b, 'TEXT', 'Катя')
proto.send_message(a, 'NICK', 'Боря'.encode('utf-8'))
show(a, 'ERROR', 'занято')
proto.send_message(a, 'NICK')
show(a, 'ERROR', 'пустым')
proto.send_message(a, 'NICK', b'\xff')
show(a, 'ERROR', 'UTF-8')
proto.send_message(a, 'TEXT', 'После смены'.encode('utf-8'))
show(b, 'TEXT', 'Катя: После смены')
proto.send_message(a, 'LIST')
names = show(a, 'LIST', 'Катя')
assert 'Аня' not in names
proto.send_message(a, 'QUIT')
show(a, 'TEXT', 'bye')
assert proto.recv_message(a) is None
a.close()
show(b, 'TEXT', 'покинул')
proto.send_message(b, 'QUIT')
show(b, 'TEXT', 'bye')
b.close()

print('\n1. Дополнительные проверки UTF-8 и лимитов')
x, y = socket.socketpair()
proto.send_message(x, 'ОШИБКА', b'ok')
assert proto.recv_message(y) == ('ОШИБКА', b'ok')
print('Команда ОШИБКА: UTF-8 проходит без потерь.')
for command, payload in [('X' * 65, b''), ('TEXT', b'x' * (proto.MAX_MESSAGE_SIZE + 1))]:
    try:
        proto.send_message(x, command, payload)
    except ValueError as error:
        print('Отправка отклонена:', error)
    else:
        raise AssertionError('Лимит не сработал')
for command_length, payload_length in [(65, 0), (4, proto.MAX_MESSAGE_SIZE + 1)]:
    x.sendall(struct.pack(proto.HEADER_FORMAT, command_length, payload_length))
    try:
        proto.recv_message(y)
    except ValueError as error:
        print('Получение отклонено до чтения тела:', error)
    else:
        raise AssertionError('Лимит не сработал')
x.close()
y.close()

print('\n2. Клиент: нет ввода имени (полные 15 секунд)')
env = dict(os.environ, PYTHONIOENCODING='utf-8')
started = time.monotonic()
process = subprocess.Popen([sys.executable, '-u', str(ROOT / 'client.py')], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
# stdin остаётся открытым без данных — имитируем забытый терминал.
process.wait(timeout=20)
out = process.stdout.read().decode('utf-8')
err = process.stderr.read().decode('utf-8')
process.stdin.close()
elapsed = time.monotonic() - started
print(out.strip())
print(f'Время: {elapsed:.1f} с; код выхода: {process.returncode}; stderr: {err!r}')
assert process.returncode == 0 and not err and 14.5 <= elapsed < 20
assert 'Время на ввод имени истекло' in out

print('\n2. Клиент: имя введено вовремя, затем /nick, /list, /quit')
code = f"import sys; sys.path.insert(0, {str(ROOT)!r}); import client; client.PORT = {port}; client.main()"
process = subprocess.Popen([sys.executable, '-u', '-c', code], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
for line in ['Студент', '/nick Ученик', '/list', '/quit']:
    process.stdin.write((line + '\n').encode('utf-8'))
    process.stdin.flush()
    time.sleep(0.4)
out, err = process.communicate(timeout=5)
out = out.decode('utf-8')
err = err.decode('utf-8')
print(out.strip())
print(f'Код выхода: {process.returncode}; stderr: {err!r}')
assert process.returncode == 0 and not err
assert 'вы вошли как Студент' in out and 'теперь известен как Ученик' in out
assert '[пользователи онлайн]' in out
listener.close()
print('\nВсе проверки прошли.')
