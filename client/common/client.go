package common

import (
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	Name           string
	Surname        string
	DocumentNumber string
	Birthdate      string
	Number         string
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	var conn net.Conn
	var err error

	for i := 0; i < 5; i++ {
		conn, err = net.Dial("tcp", c.config.ServerAddress)
		if err == nil {
			c.conn = conn
			return nil
		}
		log.Infof("action: connect | result: retry | attempt: %d | error: %v", i+1, err)
		time.Sleep(2 * time.Second)
	}

	log.Criticalf("action: connect | result: fail | client_id: %v | error: %v", c.config.ID, err)
	return err
}

func (c *Client) sendBet() error {
	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.conn.Close()

	protocol := NewProtocol(c.conn)

	err := protocol.SendBet(
		c.config.ID,
		c.config.Name,
		c.config.Surname,
		c.config.DocumentNumber,
		c.config.Birthdate,
		c.config.Number,
	)
	if err != nil {
		return err
	}
	_, _, err = protocol.receive()

	if err != nil {
		return err
	}

	log.Infof(
		"action: apuesta_enviada | result: success | dni: %v | numero: %v",
		c.config.DocumentNumber,
		c.config.Number,
	)

	return nil
}

func (c *Client) StartClientLoop() {

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM)

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {

		err := c.sendBet()
		if err != nil {
			log.Errorf(
				"action: send_bet | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		select {
		case <-time.After(c.config.LoopPeriod):

		case <-sigChan:
			log.Infof(
				"action: shutdown | result: in_progress | client_id: %v | msg: SIGTERM received",
				c.config.ID,
			)
			log.Infof(
				"action: shutdown | result: success | client_id: %v",
				c.config.ID,
			)
			return
		}
	}

	log.Infof(
		"action: loop_finished | result: success | client_id: %v",
		c.config.ID,
	)
}
