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

## Mosquitto Broker Setup

If you're using the official Mosquitto broker for Home Assistant, an easy way to add a username and password to the broker is to go to "Settings" (in Home Assistant itself, not in the Mosquitto app), "People", and add a new user by clicking "Add Person", set a name —for example, `MQTT`—, check "Allow login", set a username —for example, `mqtt`—, set the password, and check "Local access only", but leave "Administrator" unchecked. This username and password should now work for authentication with the official Mosquitto broker.

## Automation Examples

```yaml
# TelegramBot: Front door open
- alias: "TelegramBot: Front door open"
  trigger:
    - trigger: state
      entity_id: binary_sensor.front_door_contact
      to: "on"
  condition:
    # [no-spam]
    - condition: not
      conditions:
        - condition: state
          entity_id: input_select.last_notified_telegram_front_door_contact
          state: "open"
    # [/no-spam]
  action:
    # [no-spam]
    - action: input_select.select_option
      target:
        entity_id: input_select.last_notified_telegram_front_door_contact
      data:
        option: "open"
    # [/no-spam]
    - action: mqtt.publish
      data_template:
        topic: "mqtt_telegram_bot/send_text/set"
        payload: >-
          {% set msg = '⚠ Front door open' %}
          {% set timeout = (as_timestamp(now()) + 5) | int | string %}
          {{ '{ "timeout": ' + timeout + ', "text": "' + msg + '" }' }}

# TelegramBot: Front door closed
- alias: "TelegramBot: Front door closed"
  trigger:
    - trigger: state
      entity_id: binary_sensor.front_door_contact
      to: "off"
  condition:
    # [no-spam]
    - condition: not
      conditions:
        - condition: state
          entity_id: input_select.last_notified_telegram_front_door_contact
          state: "closed"
    # [/no-spam]
  action:
    # [no-spam]
    - action: input_select.select_option
      target:
        entity_id: input_select.last_notified_telegram_front_door_contact
      data:
        option: "closed"
    # [/no-spam]
    - action: mqtt.publish
      data_template:
        topic: "mqtt_telegram_bot/send_text/set"
        payload: >-
          {% set msg = '🚪 Front door closed' %}
          {% set timeout = (as_timestamp(now()) + 5) | int | string %}
          {{ '{ "timeout": ' + timeout + ', "text": "' + msg + '" }' }}

# TelegramBot: Power outage
- alias: "TelegramBot: Power outage"
  trigger:
    - trigger: state
      entity_id: sensor.ups_status
      to: "On Battery"
  condition:
    # [no-spam]
    - condition: not
      conditions:
        - condition: state
          entity_id: input_select.last_notified_telegram_power_relay
          state: "off"
    # [/no-spam]
  action:
    # [no-spam]
    - action: input_select.select_option
      target:
        entity_id: input_select.last_notified_telegram_power_relay
      data:
        option: "off"
    # [/no-spam]
    - action: mqtt.publish
      data_template:
        topic: "mqtt_telegram_bot/send_text/set"
        payload: >-
          {% set msg = '⚠ Power outage' %}
          {% set timeout = (as_timestamp(now()) + 5) | int | string %}
          {{ '{ "timeout": ' + timeout + ', "text": "' + msg + '" }' }}

# TelegramBot: Power resumption
- alias: "TelegramBot: Power resumption"
  trigger:
    - trigger: state
      entity_id: sensor.ups_status
      to: "Online"
  condition:
    # [no-spam]
    - condition: not
      conditions:
        - condition: state
          entity_id: input_select.last_notified_telegram_power_relay
          state: "on"
    # [/no-spam]
  action:
    # [no-spam]
    - action: input_select.select_option
      target:
        entity_id: input_select.last_notified_telegram_power_relay
      data:
        option: "on"
    # [/no-spam]
    - action: mqtt.publish
      data_template:
        topic: "mqtt_telegram_bot/send_text/set"
        payload: >-
          {% set msg = '⚡ Power resumption' %}
          {% set timeout = (as_timestamp(now()) + 5) | int | string %}
          {{ '{ "timeout": ' + timeout + ', "text": "' + msg + '" }' }}
```

## SSL Files

When SSL is enabled and secure validation is used:
- Place certificate and key files in Home Assistant `ssl` directory.
- Reference filenames (not full paths) in options.

## Troubleshooting

- If no message is sent, verify Telegram token and chat ID first.
- Send a manual test message to your bot in Telegram to confirm the bot is active.
- If MQTT connect fails, verify broker host/port and SSL settings.
- Enable `debug: true` for detailed logs (sensitive values are masked in startup dumps).
