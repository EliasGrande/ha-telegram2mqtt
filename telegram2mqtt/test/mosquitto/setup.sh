#!/bin/sh
set -eu

mkdir -p /mosquitto/config /mosquitto/data /mosquitto/log /mosquitto/certs

if [ ! -f /mosquitto/certs/ca.crt ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /mosquitto/certs/ca.key \
    -out /mosquitto/certs/ca.crt \
    -subj "/CN=telegram2mqtt-test-ca" >/dev/null 2>&1
fi

if [ ! -f /mosquitto/certs/server.crt ]; then
  openssl req -nodes -newkey rsa:2048 \
    -keyout /mosquitto/certs/server.key \
    -out /mosquitto/certs/server.csr \
    -subj "/CN=mosquitto" >/dev/null 2>&1
  openssl x509 -req -days 365 \
    -in /mosquitto/certs/server.csr \
    -CA /mosquitto/certs/ca.crt \
    -CAkey /mosquitto/certs/ca.key \
    -CAcreateserial \
    -out /mosquitto/certs/server.crt >/dev/null 2>&1
fi

mosquitto_passwd -b -c /mosquitto/config/passwd mqtt ExamplePassword123
chown -R mosquitto:mosquitto /mosquitto/certs
chown mosquitto:mosquitto /mosquitto/config/passwd /mosquitto/config/mosquitto.conf
chmod 600 /mosquitto/config/passwd /mosquitto/certs/server.key
chmod 644 /mosquitto/config/mosquitto.conf /mosquitto/certs/ca.crt /mosquitto/certs/server.crt
exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
