#!/bin/bash

SERVER_CONTAINER="ceng435server"
CLIENT_CONTAINER="ceng435client"

netem_command() {
    local command=$1

    # Clear all rules
    docker exec ${SERVER_CONTAINER} tc qdisc del dev eth0 root
    docker exec ${CLIENT_CONTAINER} tc qdisc del dev eth0 root

    # Add the new rule
    docker exec ${SERVER_CONTAINER} tc qdisc add dev eth0 root netem ${command}
    docker exec ${CLIENT_CONTAINER} tc qdisc add dev eth0 root netem ${command}

    # Run the experiment
    python3 main.py ${command}

    sleep 1
}

# Array of netem commands
netem_commands=(
    "loss 0%"
    "loss 5%"
    # "loss 10%"
    # "duplicate 0%"
    # "duplicate 5%"
    # "duplicate 10%"
    # "corrupt 0%"
    # "corrupt 5%"
    # "corrupt 10%"
    # "delay 100ms"
    # "delay 100ms distribution normal"
)

# First do without any netem commands
python3 main.py baseline

# Loop through each netem command
for command in ${netem_commands[@]}
do
    netem_command "${command}"
done

