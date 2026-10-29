import json
import socket
import struct
import sys
from queue import Queue

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


HOST = "127.0.0.1"
PORT = 50505


class NetCom:
    def __init__(self, sock):
        self.sock = sock

    @staticmethod
    def _recv_exact(sock, size):
        chunks = []
        received = 0
        while received < size:
            chunk = sock.recv(size - received)
            if not chunk:
                return None
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)

    def recv(self):
        header = self._recv_exact(self.sock, 4)
        if header is None:
            return None

        payload_size = struct.unpack("!I", header)[0]
        payload = self._recv_exact(self.sock, payload_size)
        if payload is None:
            return None

        return json.loads(payload.decode("utf-8"))

    def send(self, message):
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
        header = struct.pack("!I", len(payload))
        self.sock.sendall(header + payload)


class ReceiveThread(QThread):
    message_received = pyqtSignal(dict)
    disconnected = pyqtSignal(str) # 1 пункт дз

    def __init__(self, net):
        super().__init__()
        self.net = net

    def run(self):
        while True:
            try:
                message = self.net.recv()
            except OSError:
                self.disconnected.emit("Ошибка соединения с сервером") # 1 пункт дз
                break

            if message is None:
                self.disconnected.emit("Соединение потеряно") # 1 пункт дз
                break
            self.message_received.emit(message)


class SendThread(QThread):
    disconnected = pyqtSignal(str)

    def __init__(self, net):
        super().__init__()
        self.net = net
        self.queue = Queue()

    def send(self, message):
        self.queue.put(message)

    def run(self): # 2 пункт дз
        while True:
            message = self.queue.get()

            if message is None:
                break

            try:
                self.net.send(message)
            except OSError:
                self.disconnected.emit("Ошибка отправки: соединение потеряно")
                break
    def stop_queue(self): # 2 пункт дз
        self.queue.put(None)



class MainWindow(QMainWindow):
    def __init__(self, net):
        super().__init__()
        self.net = net

        self.setWindowTitle("PyQt6 network chat")
        self.resize(560, 420)

        self.history = QTextEdit()
        self.history.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message…")

        self.send_button = QPushButton("Send")
        self.status_label = QLabel("Connected to 127.0.0.1:50505")

        # name, пункт 1
        layout = QVBoxLayout()
        self.name_client = QLineEdit()
        layout.addWidget(self.name_client)
        self.name_client.setPlaceholderText('Введите имя')

        self.clear_button = QPushButton('Очистить чат') #доп задание


        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_button)


        layout.addWidget(self.status_label)
        layout.addWidget(self.history)
        layout.addWidget(self.clear_button)
        layout.addLayout(input_row)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.send_button.clicked.connect(self.on_send_clicked)
        self.input.returnPressed.connect(self.on_send_clicked) # пункт 3
        self.clear_button.clicked.connect(self.history.clear) # пункт доп 5

        self.receive_thread = ReceiveThread(self.net)
        self.receive_thread.message_received.connect(self.handle_message)
        self.receive_thread.disconnected.connect(self.handle_disconnect) # 1 пункт дз
        self.receive_thread.start()

        self.send_thread = SendThread(self.net)
        self.send_thread.disconnected.connect(self.handle_disconnect) # 2 пункт дз
        self.send_thread.start()

    def on_send_clicked(self):
        # пункт 2 , сделали на паре
        text = self.input.text().strip()
        username = self.name_client.text().strip()
        if not text:
            return

        self.send_thread.send({
            "type": "chat",
            'username': username,
            "text": text,

        })

        self.input.clear()

    def handle_message(self, message):
        if message.get("type") == "chat":
            username = message.get('username')
            text = message.get("text", "")
            self.history.append(f'{username}: {text}')
        elif message.get('type') == 'system':
            text = message.get("text", "") # 4 пункт
            self.history.append(f'[Система]: {text}')

    def handle_disconnect(self, reason): # 1 и 2 пункт дз
        self.status_label.setText(reason)
        self.send_button.setEnabled(False)
        self.input.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.name_client.setEnabled(False)

    def closeEvent(self, event): # 2 пункт дз
        self.send_thread.stop_queue()

        try:
            self.net.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        self.net.sock.close()

        self.send_thread.wait()
        self.receive_thread.wait()
        event.accept()

    def history_clear(self):
        pass
def main():
    app = QApplication(sys.argv)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except OSError as exc:
        print(f"Could not connect to server at {HOST}:{PORT}: {exc}")
        print("Run server.py first, then start main.py.")
        return

    net = NetCom(sock)
    window = MainWindow(net)
    window.show()

    exit_code = app.exec()

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    sock.close()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()