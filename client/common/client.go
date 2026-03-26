package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	MaxAmount     int
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
		log.Infof("action: connect | result: in_progress | attempt: %d | error: %v", i+1, err)
		time.Sleep(2 * time.Second)
	}

	log.Criticalf("action: connect | result: fail | client_id: %v | error: %v", c.config.ID, err)
	return err
}

func (c *Client) sendBatch(protocol *Protocol, batch []string) error {
	if err := protocol.SendBatch(batch); err != nil {
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

func (c *Client) sendAllBets(sigChan <-chan os.Signal, protocol *Protocol) error {
	filename := fmt.Sprintf(".data/agency-%s.csv", c.config.ID)
	file, err := os.Open(filename)
	if err != nil {
		log.Errorf("action: open_file | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	batch := []string{}

	for scanner.Scan() {
		select {
		case <-sigChan:
			log.Infof("action: shutdown | result: in_progress | client_id: %v", c.config.ID)
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return fmt.Errorf("SIGTERM received")
		default:
		}

		line := scanner.Text()
		bet := fmt.Sprintf("%s,%s", c.config.ID, line)
		batch = append(batch, bet)

		if len(batch) == c.config.MaxAmount {
			if err := c.sendBatch(protocol, batch); err != nil {
				log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
				return err
			}
			batch = batch[:0]
		}
	}

	if len(batch) > 0 {
		if err := c.sendBatch(protocol, batch); err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return err
		}
	}

	return nil
}

func (c *Client) notifyDoneAndQueryWinners(protocol *Protocol) error {
	if err := protocol.send(OpDone, c.config.ID); err != nil {
		return err
	}

	opcode, _, err := protocol.receive()
	if err != nil {
		return err
	}
	if opcode != OpOK {
		return fmt.Errorf("unexpected opcode after OP_DONE: %d", opcode)
	}

	if err := protocol.SendWinnersQuery(c.config.ID); err != nil {
		return err
	}

	opcode, payload, err := protocol.receive()
	if err != nil {
		return err
	}
	if opcode != OpWinners {
		return fmt.Errorf("unexpected opcode: %d", opcode)
	}

	winners := strings.Split(payload, Delimiter)
	if payload == "" {
		winners = []string{}
	}
	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", len(winners))
	return nil
}

func (c *Client) StartClientLoop() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM)

	if err := c.createClientSocket(); err != nil {
		log.Errorf("action: connect | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	defer c.conn.Close()

	protocol := NewProtocol(c.conn)

	if err := c.sendAllBets(sigChan, protocol); err != nil {
		log.Errorf("action: send_bets | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	if err := c.notifyDoneAndQueryWinners(protocol); err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
}
