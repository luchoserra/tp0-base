#!/bin/bash

MESSAGE="helo"
NETWORK="tp0_testing_net"

RESPONSE=$(docker run --rm --network $NETWORK busybox sh -c "printf '$MESSAGE' | nc server 12345")

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi