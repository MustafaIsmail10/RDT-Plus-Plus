# docker rmi ceng435
# docker build -t ceng435 .
docker run -t -i --rm --privileged --cap-add=NET_ADMIN --name ceng435server -v ./code:/app:rw ceng435:latest bash