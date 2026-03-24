import socket
import logging
import signal
from .protocol import Protocol, OP_OK, OP_ERR
from .utils import Bet, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(("", port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                break

        self._server_socket.close()
        logging.info("action: shutdown | result: success")

    def __handle_client_connection(self, client_sock):

        protocol = Protocol(client_sock)

        try:
            payload = protocol.receive_message()
            batch = [Bet(*item) for item in payload]

            store_bets(batch)

            logging.info(
                f"action: apuesta_recibida | result: success | cantidad: {len(batch)}"
            )

            protocol.send(OP_OK)

        except Exception as e:

            logging.error(
                f"action: apuesta_recibida | result: fail | cantidad: {len(batch)} | error: {e}"
            )
            try:
                protocol.send(OP_ERR, str(e))
            except Exception:
                pass

        finally:
            client_sock.close()

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
        logging.info("action: shutdown | result: in_progress")
        self._running = False
        self._server_socket.close()
