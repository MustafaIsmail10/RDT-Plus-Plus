#!/bin/bash

SERVER_CONTAINER="ceng435server"
CLIENT_CONTAINER="ceng435client"

netem_command() {
    local command=$1

    # Clear all rules
    docker exec ${SERVER_CONTAINER} tc qdisc del dev eth0 root
    docker exec ${CLIENT_CONTAINER} tc qdisc del dev eth0 root

    # Add the new rule
    docker exec ${SERVER_CONTAINER} bash -c "tc qdisc add dev eth0 root netem ${command}"
    docker exec ${CLIENT_CONTAINER} bash -c "tc qdisc add dev eth0 root netem ${command}"

    echo "Running python main.py"
    # Run the experiment
    docker exec ${CLIENT_CONTAINER} bash -c "
    cd /app/experiments/ &&
    python3 main.py ${command} 2
    "

    sleep 10
}

# Array of netem commands
netem_commands=(
    # "loss 0%"
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


# SCRIPT EXECUTION STARTS HERE
docker stop $(docker ps -a -q)
docker container prune -f

# Run Server and Client containers as detached
docker run -d -t --rm --privileged --cap-add=NET_ADMIN --name ${SERVER_CONTAINER} -v ./code:/app:rw ceng435:latest bash
docker run -d -t --rm --privileged --cap-add=NET_ADMIN --name ${CLIENT_CONTAINER} -v ./code:/app:rw ceng435:latest bash

# Start udp server
docker exec ${SERVER_CONTAINER} bash -c "
cd objects &&
./generateobjects.sh &&
cd /app/udp/ &&
python3 -u server_udp.py &
"
# docker exec ${SERVER_CONTAINER} bash -c "~/objects/generateobjects.sh"
# docker exec ${SERVER_CONTAINER} bash -c "python3 -u /app/udp/server_udp.py"

# Start tcp server
docker exec ${SERVER_CONTAINER} bash -c "
cd /app/tcp/ &&
python3 -u server_tcp.py &
"

# First do without any netem commands
# python3 main.py baseline

# Loop through each netem command
for command in ${netem_commands[@]}
do
    echo "Running experiment with command: ${command}"
    netem_command "${command}"
done

