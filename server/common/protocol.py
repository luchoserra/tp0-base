from .utils import Bet

DELIMITER = ","

OP_OK = 0
OP_BET = 1
OP_ERR = 2

HEADER_LEN = 4
OPCODE_LEN = 1


class Protocol:
    def __init__(self, sock):
        self.sock = sock

    def _recv_all(self, length):
        data = b""
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("socket closed")
            data += chunk
        return data

    def receive(self):
        opcode_bytes = self._recv_all(OPCODE_LEN)
        opcode = opcode_bytes[0]

        header = self._recv_all(HEADER_LEN)
        length = int.from_bytes(header, byteorder="big", signed=False)

        payload = ""

        if length > 0:
            payload = self._recv_all(length).decode("utf-8")

        return opcode, payload

    def send(self, opcode: int, message: str = ""):
        data = message.encode("utf-8")

        header = len(data).to_bytes(HEADER_LEN, "big")

        packet = bytes([opcode]) + header + data
        self.sock.sendall(packet)

    def receive_message(self):
        opcode, payload = self.receive()

        if opcode == OP_BET:
            fields = payload.split(DELIMITER)
            return ("BET", self._parse_bet(fields))

        else:
            raise ValueError("unknown opcode")

    def send_ok(self):
        self.send(OP_OK)

    def send_error(self, msg: str):
        self.send(OP_ERR, msg)

    def _parse_bet(self, fields) -> Bet:
        if len(fields) != 6:
            raise ValueError("invalid bet format")

        agency, nombre, apellido, dni, nacimiento, numero = fields
        print(fields)
        return Bet(
            agency,
            nombre,
            apellido,
            dni,
            nacimiento,
            numero,
        )
