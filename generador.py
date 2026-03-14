import sys

archivo = sys.argv[1]
clientes = int(sys.argv[2])

with open(archivo, "w") as f:
    f.write("name: tp0\n")
    f.write("services:\n")

    f.write("  server:\n")
    f.write("    container_name: server\n")
    f.write("    image: server:latest\n")
    f.write("    entrypoint: python3 /main.py\n")
    f.write("    environment:\n")
    f.write("      - PYTHONUNBUFFERED=1\n")
    f.write("      - LOGGING_LEVEL=DEBUG\n")
    f.write("    networks:\n")
    f.write("      - testing_net\n\n")

    for i in range(1, clientes + 1):
        f.write(f"  client{i}:\n")
        f.write(f"    container_name: client{i}\n")
        f.write("    image: client:latest\n")
        f.write("    entrypoint: /client\n")
        f.write("    environment:\n")
        f.write(f"      - CLI_ID={i}\n")
        f.write("      - CLI_LOG_LEVEL=DEBUG\n")
        f.write("    networks:\n")
        f.write("      - testing_net\n")
        f.write("    depends_on:\n")
        f.write("      - server\n\n")

    f.write("networks:\n")
    f.write("  testing_net:\n")
    f.write("    ipam:\n")
    f.write("      driver: default\n")
    f.write("      config:\n")
    f.write("        - subnet: 172.25.125.0/24\n")
