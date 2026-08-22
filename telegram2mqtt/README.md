# Telegram2MQTT

Telegram2MQTT is a Home Assistant app that bridges MQTT messages to Telegram bot messages.

## What This App Does

- Listens to a `send` MQTT command topic and forwards messages to Telegram.
- Publishes `availability` and `state` MQTT topics for Home Assistant automations.

## Installation

1. In Home Assistant, add this repository URL:
	- https://github.com/EliasGrande/ha-telegram2mqtt
2. Install the Telegram2MQTT app.
3. Create a Telegram bot with `@BotFather` and copy the bot token.
4. Get your Telegram chat ID (for example with `@userinfobot`).
5. Configure required fields:
	- `telegram_api_token`
	- `telegram_chat_id`
4. Configure MQTT fields according to your broker.
5. Start the app and verify logs.

## More Details

See full configuration reference in `DOCS.md`.