package common

import (
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"
	"bufio"
	"fmt"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	MaxAmount      int

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
func (c *Client) sendBatch(batch []string) error {

	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.conn.Close()

	protocol := NewProtocol(c.conn)

	err := protocol.SendBatch(batch)
	if err != nil {
		return err
	}
	opcode, _, err := protocol.receive()

	if err != nil {
		return err
	}

	if opcode != OpOK {
		return fmt.Errorf("server responded with error")
	}

	return nil
}

func (c *Client) StartClientLoop() {

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM)

	filename := fmt.Sprintf(".data/agency-%s.csv", c.config.ID)

	file, err := os.Open(filename)
	if err != nil {
		log.Errorf(
			"action: open_file | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	batch := []string{}

	for scanner.Scan() {

		select {
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
		default:
		}

		line := scanner.Text()
		bet := fmt.Sprintf("%s,%s", c.config.ID, line)
		batch = append(batch, bet)

		if len(batch) == c.config.MaxAmount {

			err := c.sendBatch(batch)
			if err != nil {
				log.Errorf(
					"action: send_batch | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			batch = batch[:0]
		}
	}

	if len(batch) > 0 {
		err := c.sendBatch(batch)
		if err != nil {
			log.Errorf(
				"action: send_batch | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
	}

	log.Infof(
		"action: loop_finished | result: success | client_id: %v",
		c.config.ID,
	)
}