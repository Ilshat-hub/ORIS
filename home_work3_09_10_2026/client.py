import socket

HOST = "127.0.0.1"
PORT = 5555


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        print("Команды: /add <текст>, /list, /done <номер>, /quit, /help")

        with sock.makefile("r", encoding="utf-8") as reader:
            while True:
                command = input("> ").strip()
                sock.sendall((command + "\n").encode("utf-8"))

                # Читаем ответ до пустой строки: список может занимать несколько строк.
                while True:
                    line = reader.readline()
                    if not line:
                        print("Соединение с сервером закрыто")
                        return
                    if line == "\n":
                        break
                    print(line.rstrip("\n"))

                if command == "/quit":
                    break

    except (EOFError, KeyboardInterrupt):
        print("\nКлиент завершил работу")
    except (OSError, UnicodeError) as error:
        print(f"Ошибка соединения: {error}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
