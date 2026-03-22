from .utils import Bet

DELIMITER = ","

OP_OK = 0
OP_BET = 1
OP_ERR = 2

HEADER_LEN = 4
OPCODE_LEN = 1


class Protocol:
    def __init__(self, sock):
        """Initialize the Protocol with a socket-like object."""
        self.sock = sock

    def _recv_all(self, length):
        """Read exactly `length` bytes from the socket and return them as bytes"""
        data = b""
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("socket closed")
            data += chunk
        return data

    def receive(self):
        """Receive a single framed packet and return its opcode and payload as a tuple."""
        opcode_bytes = self._recv_all(OPCODE_LEN)
        opcode = opcode_bytes[0]

        header = self._recv_all(HEADER_LEN)
        length = int.from_bytes(header, byteorder="big", signed=False)

        payload = ""

        if length > 0:
            payload = self._recv_all(length).decode("utf-8")

        return opcode, payload

    def send(self, opcode: int, message: str = ""):
        """Send a framed packet with the given opcode and UTF-8 payload."""
        data = message.encode("utf-8")

        header = len(data).to_bytes(HEADER_LEN, "big")

        packet = bytes([opcode]) + header + data
        self.sock.sendall(packet)

    def receive_message(self) -> Bet:
        """Receive a Bet message (expects opcode OP_BET), parse it and returns it"""
        opcode, payload = self.receive()

        if opcode != OP_BET:
            raise ValueError("unknown opcode")

        fields = payload.split(DELIMITER)
        return self._parse_bet(fields)

    def send_ok(self):
        """Send an OP_OK packet (empty payload)."""
        self.send(OP_OK)

    def send_error(self, msg: str):
        """Send an OP_ERR packet with the provided error message as payload."""
        self.send(OP_ERR, msg)

    def _parse_bet(self, fields) -> Bet:
        """Parse a list of fields into a Bet object and returns it."""
        if len(fields) != 6:
            raise ValueError("invalid bet format")

        agency, nombre, apellido, dni, nacimiento, numero = fields
        return Bet(
            agency,
            nombre,
            apellido,
            dni,
            nacimiento,
            numero,
        )
