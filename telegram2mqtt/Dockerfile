ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Install required packages
RUN apk add --no-cache python3 py3-pip py3-requests py3-yaml py3-paho-mqtt

# Copy the files
COPY src/ /app/

# Set the working directory
WORKDIR /app

# Use the S6 init system
ENTRYPOINT ["/init"]
CMD [ "python3", "main.py" ]