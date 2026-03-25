import socket
import logging
import signal
import os
from .protocol import (
    Protocol,
    OP_OK,
    OP_ERR,
    OP_BET,
    OP_DONE,
    OP_WINNERS,
    OP_NOT_READY,
    DELIMITER,
    BET_SEPARATOR,
)
from .utils import Bet, store_bets, load_bets, has_won


class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(("", port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self._done_agencies = set()
        self._total_agencies = int(os.getenv("CLIENT_AMOUNT", "5"))
        self._winners_cache = None

    def run(self):
        """
        Main server loop.
        Accepts new connections sequentially and handles each one until the client
        finishes communicating.
        """

        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                break

        self._server_socket.close()
        logging.info("action: shutdown | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Handle a single client connection in a loop until the client finishes sending bets
        and notifies the server with OP_DONE.
        """

        protocol = Protocol(client_sock)

        try:
            while True:
                try:
                    opcode, payload = protocol.receive()
                except ConnectionError:
                    break

                if opcode == OP_BET:
                    self._handle_bets(protocol, payload)
                elif opcode == OP_DONE:
                    self._handle_done(protocol, payload)
                    return
                elif opcode == OP_WINNERS:
                    self._handle_winners_query(protocol, payload)
                    return
                else:
                    protocol.send(OP_ERR, "unknown opcode")
                    break
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")

        client_sock.close()

    def _handle_bets(self, protocol, payload):
        """Parse and store a batch of bets from the payload, then acknowledge with OP_OK."""
        batch = []
        try:
            lines = payload.strip().split(BET_SEPARATOR)
            batch = [Bet(*line.split(DELIMITER)) for line in lines]
            store_bets(batch)
            logging.info(
                f"action: apuesta_recibida | result: success | cantidad: {len(batch)}"
            )
            protocol.send(OP_OK)
        except Exception as e:
            logging.error(
                f"action: apuesta_recibida | result: fail | cantidad: {len(batch)} | error: {e}"
            )
            protocol.send(OP_ERR, str(e))

    def _handle_done(self, protocol, payload):
        """Register the agency as done sending bets and acknowledge."""
        agency = payload
        self._done_agencies.add(agency)
        logging.info(
            f"action: agency_done | result: success | agency: {agency} | total: {len(self._done_agencies)}"
        )
        protocol.send(OP_OK)

    def _handle_winners_query(self, protocol, payload):
        """Respond with winners if all agencies are done, otherwise respond with OP_NOT_READY."""
        agency = payload

        if len(self._done_agencies) < self._total_agencies:
            protocol.send(OP_NOT_READY)
            return

        if self._winners_cache is None:
            logging.info("action: sorteo | result: success")
            self._winners_cache = {}
            for bet in load_bets():
                if has_won(bet):
                    self._winners_cache.setdefault(str(bet.agency), []).append(bet.document)

        winners = self._winners_cache.get(agency, [])
        protocol.send(OP_WINNERS, DELIMITER.join(winners))

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info("action: accept_connections | result: in_progress")
        c, addr = self._server_socket.accept()
        logging.info(f"action: accept_connections | result: success | ip: {addr[0]}")
        return c

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM by stopping the main loop and closing the server socket."""
        logging.info("action: shutdown | result: in_progress")
        self._running = False
        self._server_socket.close()
