package common

import (
	"encoding/binary"
	"errors"
	"net"
	"strings"
)

const (
	OpOK  byte = 0
	OpBet byte = 1
	OpErr byte = 2

	OpcodeLen = 1
	HeaderLen = 4

	Delimiter = ","
)

type Protocol struct {
	conn net.Conn
}

func NewProtocol(conn net.Conn) *Protocol {
	return &Protocol{conn: conn}
}

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

func (p *Protocol) ReceiveResponse() error {

	opcode, payload, err := p.receive()
	if err != nil {
		return err
	}

	switch opcode {

	case OpOK:
		return nil

	case OpErr:
		return errors.New(payload)

	default:
		return errors.New("unknown opcode")
	}
}
