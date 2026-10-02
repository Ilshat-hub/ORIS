import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

clients = {}
clients_lock = threading.Lock()


def broadcast(command, text, exclude=None):
    payload = text.encode("utf-8")
    with clients_lock:
        targets = [s for s in clients if s is not exclude]
    for sock in targets:
        try:
            proto.send_message(sock, command, payload)
        except (BrokenPipeError, ConnectionResetError, OSError) as error:
            print(f"[!] не удалось доставить сообщение: {error}")


def handle_client(sock, addr):
    username = None
    try:
        first = proto.recv_message(sock)
        if first is None or first[0] != "JOIN":
            proto.send_message(sock, "ERROR", b"first command must be JOIN")
            return

        # Имя читаем строго: повреждённый UTF-8 — это ошибка запроса.
        requested_name = first[1].decode("utf-8").strip()
        with clients_lock:
            if not requested_name or requested_name in clients.values():
                proto.send_message(sock, "ERROR", b"invalid or taken username")
                return
            username = requested_name
            clients[sock] = username

        proto.send_message(sock, "TEXT", f"* вы вошли как {username}".encode())
        broadcast("TEXT", f"* {username} присоединился", exclude=sock)
        print(f"[+] {username} присоединился ({addr})")

        while True:
            msg = proto.recv_message(sock)
            if msg is None:
                print(f"[i] {username} отключился без QUIT")
                break

            command, payload = msg
            if command == "TEXT":
                text = payload.decode("utf-8", errors="replace")
                broadcast("TEXT", f"{username}: {text}", exclude=sock)
            elif command == "LIST":
                with clients_lock:
                    names = list(clients.values())
                proto.send_message(sock, "LIST", "\n".join(names).encode())
            elif command == "NICK":
                # ДЗ 3: проверка и смена под одним замком. Иначе два
                # клиента могли бы одновременно забрать одинаковое имя.
                try:
                    new_name = payload.decode("utf-8").strip()
                except UnicodeDecodeError:
                    proto.send_message(sock, "ERROR", "Имя должно быть в UTF-8".encode("utf-8"))
                    continue
                with clients_lock:
                    if not new_name:
                        error = "Новое имя не должно быть пустым"
                    elif any(name == new_name and other is not sock
                             for other, name in clients.items()):
                        error = "Это имя уже занято"
                    else:
                        error = None
                        old_name = username
                        username = new_name
                        clients[sock] = username
                if error:
                    proto.send_message(sock, "ERROR", error.encode("utf-8"))
                else:
                    broadcast("TEXT", f"* {old_name} теперь известен как {username}")
                    print(f"[nick] {old_name} -> {username}")
            elif command == "QUIT":
                proto.send_message(sock, "TEXT", b"* bye")
                print(f"[-] {username} вышел через QUIT")
                break
            else:
                proto.send_message(sock, "ERROR", f"unknown command {command}".encode())

    except ConnectionResetError:
        print(f"[!] {username or addr} - соединение сброшено (RST)")
    except BrokenPipeError:
        print(f"[!] {username or addr} - не удалось отправить, соединение разорвано")
    except ValueError as error:
        # Ошибочный кадр нельзя продолжать читать: границы уже ненадёжны.
        print(f"[!] некорректный запрос от {username or addr}: {error}")
        try:
            proto.send_message(sock, "ERROR", f"Некорректный запрос: {error}".encode("utf-8"))
        except (ConnectionError, OSError) as send_error:
            print(f"[!] ответ с ошибкой не доставлен: {send_error}")
    except (ConnectionError, OSError) as error:
        print(f"[!] {username or addr} - ошибка соединения: {error}")
    finally:
        with clients_lock:
            clients.pop(sock, None)
        sock.close()
        if username:
            broadcast("TEXT", f"* {username} покинул чат")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] сервер слушает {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] сервер остановлен")