#!/bin/bash

cd "$(dirname "$0")" || exit 1

COMPOSE_FILE=$(realpath "docker-compose.yml")

# Build and run
echo "Building and running the Docker container using Docker Compose..."
docker-compose -f "$COMPOSE_FILE" up --build --abort-on-container-exit --exit-code-from verifier
TEST_EXIT_CODE=$?

# Clean
echo "Cleaning up..."
docker-compose -f "$COMPOSE_FILE" down --rmi all

echo
if [ "$TEST_EXIT_CODE" -eq 0 ]; then
	echo "TEST RESULT: PASS"
else
	echo "TEST RESULT: FAIL"
fi

exit "$TEST_EXIT_CODE"