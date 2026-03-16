#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./generar-compose.sh <output_file> <number_of_clients>"
    exit 1
fi

OUTPUT_FILE=$1
NUM_CLIENTS=$2

if ! [[ "$NUM_CLIENTS" =~ ^[0-9]+$ ]]; then
    echo "Error: number_of_clients must be an integer"
    exit 1
fi

echo "Output file name: $OUTPUT_FILE"
echo "Number of clients: $NUM_CLIENTS"

python3 generador.py "$OUTPUT_FILE" "$NUM_CLIENTS"