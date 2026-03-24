package common

import (
	"encoding/binary"
	"net"
	"strings"
)

const (
	OpOK  byte = 0
	OpBet byte = 1
	OpErr byte = 2

	OpcodeLen = 1
	HeaderLen = 4

	Delimiter   = ","
	BetSeparator = "\n"
)

type Protocol struct {
	conn net.Conn
}

// NewProtocol returns a new Protocol that wraps the given network connection.
func NewProtocol(conn net.Conn) *Protocol {
	return &Protocol{conn: conn}
}

// Sends a framed packet to the Server.
// Returns an error if any write fails.
func (p *Protocol) send(opcode byte, message string) error {
	data := []byte(message)

	length := make([]byte, HeaderLen)
	binary.BigEndian.PutUint32(length, uint32(len(data)))

	packet := append([]byte{opcode}, length...)
	packet = append(packet, data...)

	total := 0
	for total < len(packet) {
		n, err := p.conn.Write(packet[total:])
		if err != nil {
			return err
		}
		total += n
	}

	return nil
}

// recvAll reads exactly length bytes from the Server, returning the data it read.
func (p *Protocol) recvAll(length int) ([]byte, error) {
	data := make([]byte, length)
	total := 0

	for total < length {
		n, err := p.conn.Read(data[total:])
		if err != nil {
			return nil, err
		}
		total += n
	}

	return data, nil
}

// receive reads a single framed packet from the Server.
// It returns the opcode, payload string and an error if one occurred.
func (p *Protocol) receive() (byte, string, error) {

	opcodeBytes, err := p.recvAll(OpcodeLen)
	if err != nil {
		return 0, "", err
	}

	opcode := opcodeBytes[0]

	header, err := p.recvAll(HeaderLen)
	if err != nil {
		return 0, "", err
	}

	length := binary.BigEndian.Uint32(header)

	payload, err := p.recvAll(int(length))
	if err != nil {
		return 0, "", err
	}

	return opcode, string(payload), nil
}

// SendBet builds a bet payload from the provided fields and sends it using the OpBet opcode.
func (p *Protocol) SendBet(
	agency string,
	nombre string,
	apellido string,
	dni string,
	nacimiento string,
	numero string,
) error {

	parts := []string{agency, nombre, apellido, dni, nacimiento, numero}
	payload := strings.Join(parts, Delimiter)

	return p.send(OpBet, payload)
}

func (p *Protocol) SendBatch(bets []string) error {

	payload := strings.Join(bets, BetSeparator)

	return p.send(OpBet, payload)
}