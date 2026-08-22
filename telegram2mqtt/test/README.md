# Local Test Stack

This folder contains a self-contained Docker Compose stack for local testing.

Services:
- `mosquitto`: local MQTT broker with TLS and password authentication.
- `telegram2mqtt`: the app under test.
- `telegram-mock`: local HTTP server that captures outgoing Telegram requests.
- `verifier`: waits for MQTT availability and validates basic send flow behavior.

Expected behavior:
- The app publishes `running/available` as `online`.
- An expired test message is ignored.
- A valid test message reaches the local Telegram mock.

Launchers:
- Linux/macOS shell: `run-linux.sh`
- Windows: `run-windows.bat`

Notes:
- The stack uses local test options from `test/data/options.yaml`.
- No real Telegram API or external MQTT broker is required.
