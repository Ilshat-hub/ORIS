import struct

# ДЗ 1: в заголовке теперь две длины, а сама команда идёт после него.
# ! — сетевой порядок байтов; I — целое число размером 4 байта.
MAX_COMMAND_SIZE = 64
HEADER_FORMAT = "!II"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_MESSAGE_SIZE = 10 * 1024 * 1024


def recv_exact(sock, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("соединение закрыто до получения всех данных")
        chunks.extend(chunk)
    return bytes(chunks)


def send_message(sock, command, payload=b""):
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError(f"payload слишком большой: {len(payload)} байт")
    command_bytes = command.encode("utf-8")
    # Считаем байты, а не буквы: кириллица занимает больше одного байта.
    if not 1 <= len(command_bytes) <= MAX_COMMAND_SIZE:
        raise ValueError("длина команды должна быть от 1 до 64 байт")
    header = struct.pack(HEADER_FORMAT, len(command_bytes), len(payload))
    # ERROR больше не теряет последнюю букву — ей теперь хватает места
    sock.sendall(header + command_bytes + payload)


def recv_message(sock):
    try:
        header = recv_exact(sock, HEADER_SIZE)
    except ConnectionError:
        return None
    command_length, length = struct.unpack(HEADER_FORMAT, header)
    # Проверяем длины ДО чтения тела: мегабайтная команда нам не нужна.
    if not 1 <= command_length <= MAX_COMMAND_SIZE:
        raise ValueError("заявленная длина команды должна быть от 1 до 64 байт")
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"заявленная длина {length} превышает лимит")
    command_bytes = recv_exact(sock, command_length)
    payload = recv_exact(sock, length) if length else b""
    return command_bytes.decode("utf-8"), payload