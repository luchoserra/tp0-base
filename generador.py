import sys


def generar_server():
    return """  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net

"""


def generar_cliente(i):
    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server

"""


def generar_network():
    return """networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""


def main():
    archivo = sys.argv[1]
    clientes = int(sys.argv[2])

    with open(archivo, "w") as f:
        f.write("name: tp0\n")
        f.write("services:\n")

        f.write(generar_server())

        for i in range(1, clientes + 1):
            f.write(generar_cliente(i))

        f.write(generar_network())


if __name__ == "__main__":
    main()
