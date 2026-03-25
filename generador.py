import sys


def generate_server(clientes):
    """Generate the YAML configuration for the server container."""

    return f"""  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - CLIENT_AMOUNT={clientes}
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini

"""


def generate_client(i):
    """Generate the YAML configuration for a client container."""

    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
      - ./.data:/.data

"""


def generate_network():
    """Generate the YAML configuration for the testing network."""

    return """networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""


def main():
    """
    Generates a docker-compose with a server and N clients.
    """

    if len(sys.argv) != 3:
        print("Usage: python3 mi-generador.py <output_file> <number_of_clients>")
        sys.exit(1)

    archivo = sys.argv[1]

    try:
        clientes = int(sys.argv[2])
    except ValueError:
        print("Error: number_of_clients must be an integer")
        sys.exit(1)

    with open(archivo, "w") as f:
        f.write("name: tp0\n")
        f.write("services:\n")

        f.write(generate_server(clientes))

        for i in range(1, clientes + 1):
            f.write(generate_client(i))

        f.write(generate_network())

    print("Compose generated correctly.")


if __name__ == "__main__":
    main()
