import socket
import logging
import signal
from .protocol import Protocol
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
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        protocol = Protocol(client_sock)

        try:
            payload = protocol.receive_message()
            bet = Bet(*payload)
            store_bets([bet])

            logging.info(
                f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}"
            )

            protocol.send_ok()

        except Exception as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            try:
                protocol.send_error(str(e))
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
