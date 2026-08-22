# Telegram2MQTT App Documentation

## Overview

This Home Assistant app sends Telegram bot messages from MQTT commands and exposes runtime sensors over MQTT.

## MQTT Topics

Using default `mqtt_base_topic: mqtt_telegram_bot`:
- Availability sensor: `mqtt_telegram_bot/running/available`
- Running state sensor: `mqtt_telegram_bot/running/state`
- Send message over Telegram topic: `mqtt_telegram_bot/send_text/set`

## MQTT Command Contract

Publish JSON payloads to:
- `{mqtt_base_topic}/send_text/set`

Example:
```json
{
	"timeout": 1730000000,
	"text": "Service notification",
	"private": false
}
```

Behavior:
- Expired messages (`timeout` in the past) are ignored.
- Messages are sent to configured `telegram_chat_id`.

## Quick Start

1. Create your Telegram bot with `@BotFather`.
2. Get your chat ID.
3. Fill in app configuration in Home Assistant.
4. Start the app.
5. Publish a test message to MQTT.

## Telegram Setup

### 1. Create a Bot Token with @BotFather

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts.
3. Copy the token it returns.
4. Paste that value into `telegram_api_token` in the app configuration.

### 2. Get Your Chat ID

Option A (simple):
1. Open `@userinfobot`.
2. Send `/start`.
3. Copy your numeric ID.
4. Paste it into `telegram_chat_id`.

Option B (group chats):
1. Add your bot to the group.
2. Send at least one message in that group.
3. Use a chat ID helper bot/API to retrieve the group chat ID.
4. Set that value in `telegram_chat_id`.

## Required Configuration

- `telegram_api_token` (string)
- `telegram_chat_id` (integer)

## Optional Configuration

### MQTT

- `mqtt_host` (default: `homeassistant.local`)
- `mqtt_port` (default: `8883`)
- `mqtt_user` (optional)
- `mqtt_pass` (optional, required when `mqtt_user` is set)
- `mqtt_ssl_enabled` (default: `true`)
- `mqtt_ssl_insecure` (default: `false`)
- `mqtt_ssl_certfile` (default: `fullchain.pem`)
- `mqtt_ssl_keyfile` (default: `privkey.pem`)
- `mqtt_base_topic` (default: `mqtt_telegram_bot`)
- `mqtt_republish_interval` (default: `60`)

### Telegram

- `telegram_api_url` (default: `https://api.telegram.org/bot{token}`)
- `telegram_parse_mode` (`MarkdownV2`, `HTML`, or `Markdown`)
- `telegram_message_prefix` (optional, useful to distinguish environments)
- `telegram_message_start` (startup message)
- `telegram_message_stop` (shutdown message)

### Runtime

- `debug` (default: `false`)

## SSL Files

When SSL is enabled and secure validation is used:
- Place certificate and key files in Home Assistant `ssl` directory.
- Reference filenames (not full paths) in options.

## Notes for Users

- You normally configure everything in the Home Assistant UI.
- You do not need to manually edit internal files.

## Troubleshooting

- If no message is sent, verify Telegram token and chat ID first.
- Send a manual test message to your bot in Telegram to confirm the bot is active.
- If MQTT connect fails, verify broker host/port and SSL settings.
- Enable `debug: true` for detailed logs (sensitive values are masked in startup dumps).