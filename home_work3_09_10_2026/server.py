import socket
import threading

HOST = "127.0.0.1"
PORT = 5555

tasks = []
tasks_lock = threading.Lock()


def handle_client(sock, addr):
    print(f"[+] подключился {addr}")
    try:
        with sock.makefile("r", encoding="utf-8") as reader:
            while True:
                line = reader.readline()
                if not line:
                    break

                command = line.strip()
                parts = command.split(maxsplit=1)
                name = parts[0] if parts else ""
                text = parts[1].strip() if len(parts) == 2 else ""

                if name == "/add":
                    if not text:
                        answer = "Ошибка: введите /add <текст задачи>"
                    else:
                        # Список общий, поэтому добавляем под замком.
                        with tasks_lock:
                            tasks.append({"text": text, "done": False})
                        answer = "Задача добавлена"

                elif command == "/list":
                    with tasks_lock:
                        if not tasks:
                            answer = "Список задач пуст"
                        else:
                            lines = []
                            for number, task in enumerate(tasks, start=1):
                                mark = "x" if task["done"] else " "
                                lines.append(f"{number}. [{mark}] {task['text']}")
                            answer = "\n".join(lines)

                elif name == "/done":
                    try:
                        number = int(text)
                    except ValueError:
                        answer = "Ошибка: введите /done <целый номер задачи>"
                    else:
                        # Проверяем номер и меняем задачу под одним замком.
                        with tasks_lock:
                            if number < 1 or number > len(tasks):
                                answer = "Ошибка: задачи с таким номером нет"
                            else:
                                tasks[number - 1]["done"] = True
                                answer = "Задача выполнена"

                elif command == "/quit":
                    sock.sendall("До свидания!\n\n".encode("utf-8"))
                    break
                elif command == "/help":
                    sock.sendall("/add - команда для добавления задачи\n/list - список задач\n"
                                 "/done - команда для выполнения задачи".encode("utf-8"))
                    answer = "Хорошего дня"
                else:
                    answer = "Ошибка: неизвестная команда\n"

                # Пустая строка обозначает конец ответа, в том числе для /list.
                sock.sendall((answer + "\n\n").encode("utf-8"))

    except (OSError, UnicodeError) as error:
        print(f"[!] ошибка соединения с {addr}: {error}")
    finally:
        sock.close()
        print(f"[-] отключился {addr}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] сервер слушает {HOST}:{PORT}", flush=True)
        while True:
            client_sock, addr = server.accept()
            # Для каждого клиента запускаем отдельный поток.
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] сервер остановлен")
    except OSError as error:
        print(f"[!] не удалось запустить сервер: {error}")
