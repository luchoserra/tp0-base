import socket
import logging
import signal
import os
import threading
from .protocol import (
    Protocol,
    OP_OK,
    OP_ERR,
    OP_BET,
    OP_DONE,
    OP_WINNERS,
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

        total_agencies = int(os.getenv("CLIENT_AMOUNT", "5"))
        self._barrier = threading.Barrier(total_agencies)
        self._bets_lock = threading.Lock()

    def run(self):
        """
        Main server loop.

        Accepts new connections and spawns a thread to handle each one in parallel.
        Stops when a SIGTERM is received or the socket is closed.
        """
        threads = []
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                t = threading.Thread(
                    target=self.__handle_client_connection, args=(client_sock,)
                )
                t.start()
                threads.append(t)
            except OSError:
                break

        for t in threads:
            t.join()

        self._server_socket.close()
        logging.info("action: shutdown | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Handle a single client connection, processing different client opcodes in a loop.
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
            with self._bets_lock:
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
        """
        Handles the agency's OP_DONE and wait at the barrier until all agencies are done.
        """
        agency = payload
        logging.info(f"action: agency_done | result: success | agency: {agency}")
        protocol.send(OP_OK)

        idx = self._barrier.wait()
        if idx == 0:
            logging.info("action: sorteo | result: success")

    def _handle_winners_query(self, protocol, payload):
        """
        Respond to a winners query from a client.
        """
        agency = payload
        winners = [
            bet.document
            for bet in load_bets()
            if has_won(bet) and bet.agency == int(agency)
        ]
        try:
            protocol.send(OP_WINNERS, DELIMITER.join(winners))
        except Exception as e:
            logging.error(
                f"action: send_winners | result: fail | agency: {agency} | error: {e}"
            )
        finally:
            protocol.sock.close()

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
