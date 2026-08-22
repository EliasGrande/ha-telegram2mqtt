#!/usr/bin/env python

import json
import logging
import os
import ssl

import paho.mqtt.client as mqtt
import yaml
from logging_setup import get_logger

LOGGER = get_logger('config')


def parse_bool(str_bool):
  value = str(str_bool).lower()
  if value == "true":
    return True
  elif value == "false":
    return False
  else:
    raise ValueError(f"Invalid boolean string: {value}")


def mask_passwords(data):
  if isinstance(data, dict):
    for key, value in data.items():
      if 'pass' in key.lower() or 'token' in key.lower() or 'chat_id' in key.lower():
        data[key] = '*** SECRET ***'
      else:
        data[key] = mask_passwords(value)
  elif isinstance(data, list):
    for index, item in enumerate(data):
      data[index] = mask_passwords(item)
  return data


CONFIG_YAML = '/data/options.yaml'
CONFIG_JSON = '/data/options.json'
if os.path.isfile(CONFIG_YAML):
  with open(CONFIG_YAML, 'r') as file:
    CONFIG_DICT: dict = yaml.safe_load(file.read())
else:
  with open(CONFIG_JSON, 'r') as file:
    CONFIG_DICT: dict = json.load(file)

DEBUG = bool(CONFIG_DICT.get('debug', False))


class DictConfig:
  def __init__(self, source, prop: str = None):
    # self._json_init(source, prop)
    self._snake_init(source, prop)

  def get[_VT](self, key: str, default: _VT = None, required=False) -> _VT:
    # return self._json_get(key, default, required)
    return self._snake_get(key, default, required)

  #region plain one-level snake-joint-props object

  def _snake_init(self, source, prop: str = None):
    if isinstance(source, DictConfig):
      if prop == None:
        self._key_prefix = source._key_prefix
      else:
        self._key_prefix = f'{source._key_prefix}{prop}_'
    else:
      if prop == None:
        self._key_prefix = ''
      else:
        self._key_prefix = f'{prop}_'

  def _snake_get[_VT](self, key: str, default: _VT = None, required=False) -> _VT:
    snake_key = f'{self._key_prefix}{key}'
    value = CONFIG_DICT.get(snake_key, None)
    if (value == None) or (len(str(value)) == 0):
      display_key = f'`{self._key_prefix}{key}`'
      if (required):
        raise Exception(f'Required config {display_key} not found')
      else:
        value = default
        if (default != None):
          LOGGER.info(f'Optional config {display_key} not found, using default: {default}')
    return value

  #endregion

  #region JSON nested dicts

  def _json_init(self, source, prop: str = None):
    if isinstance(source, DictConfig):
      if prop == None:
        self._dict = source._dict
        self._key_prefix = source._key_prefix
      else:
        self._dict = source._dict.get(prop, dict())
        self._key_prefix = f'{source._key_prefix}{prop}.'
    else:
      if prop == None:
        self._dict = source
        self._key_prefix = ''
      else:
        self._dict = source.get(prop, dict())
        self._key_prefix = f'{prop}.'

  def _json_get[_VT](self, key: str, default: _VT = None, required=False) -> _VT:
    value = self._dict.get(key, None)
    if (value == None) or (len(str(value)) == 0):
      display_key = f'`{self._key_prefix}{key}`'
      if (required):
        raise Exception(f'Required config {display_key} not found')
      else:
        value = default
        if (default != None):
          LOGGER.info(f'Optional config {display_key} not found, using default: {default}')
    return value

  #endregion


class SslConfig(DictConfig):
  def __init__(self, source: DictConfig, prop: str):
    super().__init__(source, prop)

    self.ENABLED: bool = self.get("enabled", True)
    """
    SSL enabled (default: `True`)
    """

    self.INSECURE: bool = self.get("insecure", False)
    """
    Skip SSL validation, for testing purposes (default: `False`)
    """

    self.CERTFILE: str = self.get("certfile", "fullchain.pem")
    """
    SSL cert file (default: `"fullchain.pem"`)
    """

    self.KEYFILE: str = self.get("keyfile", "privkey.pem")
    """
    SSL key file (default: `"privkey.pem"`)
    """


class MqttConfig(DictConfig):
  def __init__(self, source: DictConfig, prop: str):
    super().__init__(source, prop)

    self.HOST: str = self.get("host", "homeassistant.local")
    """
    MQTT host (default: `"homeassistant.local"`)
    """

    self.PORT: int = self.get("port", 8883)
    """
    MQTT port (default: `8883`)
    """

    self.USER: str = self.get("user", None)
    """
    MQTT username (default: `None`)
    """

    self.PASS: str = self.get("pass", None, self.USER != None)
    """
    MQTT password (default: `None`)
    """

    self.SSL = SslConfig(self, "ssl")
    """
    MQTT SSL config
    """

    self.BASE_TOPIC: str = self.get("base_topic", "mqtt_telegram_bot")
    """
    MQTT base topic (default: `"mqtt_telegram_bot"`)
    """

    self.REPUBLISH_INTERVAL: int = self.get('republish_interval', 60)
    """
    MQTT republish interval for sensors in seconds (default: `60`)
    """

  def single_auth(self):
    if self.USER == None:
      return None
    return {
      "username": self.USER,
      "password": self.PASS
    }

  def single_tls(self):
    if not self.SSL.ENABLED:
      return None
    if self.SSL.INSECURE:
      return {
        "insecure": True,
        "cert_reqs": ssl.CERT_NONE
      }
    return {
      # "insecure": True,
      "certfile": f'/ssl/{self.SSL.CERTFILE}',
      "keyfile": f'/ssl/{self.SSL.KEYFILE}'
    }

  def auth_set(self, client: mqtt.Client):
    if self.USER != None:
      client.username_pw_set(username=self.USER, password=self.PASS)

  def tls_set(self, client: mqtt.Client):
    if not self.SSL.ENABLED:
      return
    elif self.SSL.INSECURE:
      client.tls_set(cert_reqs=ssl.CERT_NONE)
      client.tls_insecure_set(True)
    else:
      client.tls_set(
        certfile=f'/ssl/{self.SSL.CERTFILE}',
        keyfile=f'/ssl/{self.SSL.KEYFILE}')


class TelegramConfig(DictConfig):
  def __init__(self, source: DictConfig, prop: str):
    super().__init__(source, prop)

    self.API_TOKEN: str = self.get('api_token', required=True)
    """
    Telegram API token (required)
    """

    self.API_URL: str = self.get('api_url', default='https://api.telegram.org/bot{token}').replace('{token}', self.API_TOKEN)
    """
    Telegram API url (default: `"https://api.telegram.org/bot{token}"`)

    The `"{token}"` placeholder is replaced with `self.API_TOKEN`
    """

    self.CHAT_ID: int = self.get('chat_id', required=True)
    """
    Telegram chat ID (required)
    """

    self.PARSE_MODE: str = self.get('parse_mode', 'MarkdownV2')
    """
    Telegram message parse mode (default: `"MarkdownV2"`)

    See https://core.telegram.org/bots/api#formatting-options
    """

    self.MESSAGE_PREFIX: str = self.get('message_prefix', '')
    """
    Prefix added to all the messages sent by the bot, for testing purposes (default: `""`)
    """

    self.MESSAGE_START: str = self.get('message_start', '👌 *telegram2mqtt* started')
    """
    Message sent by the bot when the app starts (default: `"👌 *telegram2mqtt* started"`)

    Icon from https://apps.timwhitlock.info/emoji/tables/unicode
    """

    self.MESSAGE_STOP: str = self.get('message_stop', '💀 *telegram2mqtt* stopped')
    """
    Message sent by the bot when the app stops (default: `"💀 *telegram2mqtt* stopped"`)

    Icon from https://apps.timwhitlock.info/emoji/tables/unicode
    """


class Config(DictConfig):
  def __init__(self):
    super().__init__(CONFIG_DICT)

    self.MQTT = MqttConfig(self, "mqtt")
    """
    MQTT config
    """

    self.TELEGRAM = TelegramConfig(self, "telegram")
    """
    Telegram config
    """

    self.DEBUG = DEBUG
    """
    DEBUG mode enabled
    """


def create_config():
  return Config()
