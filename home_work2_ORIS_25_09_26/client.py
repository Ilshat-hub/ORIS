import queue
import socket
import threading
import protocol as proto

HOST = "127.0.0.1"
PORT = 5555
USERNAME_TIMEOUT = 15  # ДЗ 2: столько секунд даём на ввод имени.



def input_username(timeout=USERNAME_TIMEOUT):
    # input блокирует только этот поток, а main ждёт очередь с таймаутом.
    # Никакого вечного опроса(серьезная часть): процессор может спокойно чилить (несерьезная часть)
    result = queue.Queue()

    def read_name():
        try:
            result.put(input("Введите имя: ").strip())
        except EOFError:
            result.put(None)

    # daemon не удержит программу, если время вышло, а input ещё ждёт
    threading.Thread(target=read_name, daemon=True).start()
    try:
        return result.get(timeout=timeout)
    except queue.Empty:
        print("\nВремя на ввод имени истекло. Клиент завершает работу.")
        return None

def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            msg = proto.recv_message(sock)
        except (ConnectionError, OSError, ValueError) as error:
            if not stop_event.is_set():
                print(f"\n[!] ошибка при получении сообщения: {error}")
            msg = None
        if msg is None:
            if not stop_event.is_set():
                print("\n[!] соединение с сервером потеряно")
            stop_event.set()
            break
        command, payload = msg
        text = payload.decode("utf-8", errors="replace")
        if command == "LIST":
            print(f"\n[пользователи онлайн]\n{text}\n> ", end="")
        elif command == "ERROR":  # ДЗ 1: принимаем полное слово
            print(f"\n[ошибка] {text}\n> ", end="")
        else:
            print(f"\n{text}\n> ", end="")


def main():
    try:
        username = input_username()
    except KeyboardInterrupt:
        print("\nВвод имени отменён.")
        return
    if username is None:
        return
    if not username:
        print("Имя не должно быть пустым.")
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        proto.send_message(sock, "JOIN", username.encode())
    except (ConnectionRefusedError, OSError) as e:
        print(f"Не удалось подключиться: {e}")
        sock.close()
        return

    stop_event = threading.Event()
    threading.Thread(target=listen_loop, args=(sock, stop_event), daemon=True).start()

    print("Команды: /list, /nick <новое_имя>, /quit. Остальной текст - сообщение в чат.")
    try:
        while not stop_event.is_set():
            line = input("> ")
            if line == "/quit":
                stop_event.set()  # Это наш выход, а не внезапная потеря связи
                proto.send_message(sock, "QUIT")
                break
            elif line == "/list":
                proto.send_message(sock, "LIST")
            # ДЗ 3: сервер сам проверит имя(серьезная часть) — клиент ему не судья :) (несерьезная часть)
            elif line == "/nick" or line.startswith("/nick "):
                proto.send_message(sock, "NICK", line[5:].strip().encode("utf-8"))
            elif line:
                proto.send_message(sock, "TEXT", line.encode())
    except (EOFError, KeyboardInterrupt):
        print("\nКлиент завершает работу.")
    except (BrokenPipeError, OSError, ValueError) as error:
        print(f"\nНе удалось отправить сообщение: {error}")
    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()