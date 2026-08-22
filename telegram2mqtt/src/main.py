#!/usr/bin/env python

# apk add --no-cache python3 py3-pip py3-requests py3-yaml py3-paho-mqtt
import time, traceback, logging, urllib, json
import requests
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from config import CONFIG_DICT, DEBUG, create_config, mask_passwords
from lifecycle import Disposable, SigtermInterrupt, exit_app, register_sigterm_handler
from logging_setup import configure_logging

LOGGER = configure_logging(CONFIG_DICT, DEBUG, mask_passwords)

CONFIG = create_config()

register_sigterm_handler()

class MqttSensor(Disposable):

  def __init__(self, manager, device_name, state, dispose_state=None):
    super().__init__(f'publisher_{device_name}')
    self.manager = manager
    self.device_name = device_name
    self.state_topic = f'{CONFIG.MQTT.BASE_TOPIC}/{device_name}/state'
    self.availability_topic = f'{CONFIG.MQTT.BASE_TOPIC}/{device_name}/available'
    self.state = state
    self.state_is_bool = type(state) is bool
    self.dispose_state = dispose_state
    self.republish()

  def _dispose(self):
    self.publish_available(False)
    if (self.dispose_state != None):
      self.publish_state(self.dispose_state)
  
  def _publish(self, topic, payload, qos=1, retain=True):
    if self._disposed: return
    host = CONFIG.MQTT.HOST
    port = CONFIG.MQTT.PORT
    LOGGER.info(f'Publish: {topic}: {payload}')
    publish.single(
      topic = topic,
      payload = payload,
      qos = qos,
      retain = retain,
      hostname = host,
      port = port,
      auth = CONFIG.MQTT.single_auth(),
      tls = CONFIG.MQTT.single_tls())
  
  def publish_available(self, value=True):
    if self._disposed: return
    payload = 'online' if value else 'offline'
    self._publish(self.availability_topic, payload)
  
  def publish_state(self, value=None):
    if self._disposed: return
    if (value == None): value = self.state
    else: self.state = value
    payload = value
    if self.state_is_bool: payload = 'on' if value else 'off'
    self._publish(self.state_topic, payload)
  
  def republish(self):
    if self._disposed: return
    self.publish_available()
    self.publish_state()

class MqttSubscriber(Disposable):

  def __init__(self, manager, device_name):
    super().__init__(f'subscriber_{device_name}')
    self.manager = manager
    self.device_name = device_name
    self.set_topic = f'{CONFIG.MQTT.BASE_TOPIC}/{device_name}/set'
    client = self.client = mqtt.Client(device_name)
    CONFIG.MQTT.tls_set(client)
    CONFIG.MQTT.auth_set(client)
    def on_subscribe(client, userdata, mid, granted_qos): self.on_subscribe(userdata, mid, granted_qos)
    def on_connect(client, userdata, flags, rc): self.on_connect(userdata, flags, rc)
    def on_message(client, userdata, msg): self.on_message(userdata, msg)
    self._on_subscribe_notified = False
    client.on_subscribe = on_subscribe
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(CONFIG.MQTT.HOST, CONFIG.MQTT.PORT)
    client.loop_start()
  
  def _dispose(self):
    self.client.unsubscribe(self.set_topic)
    self.client.loop_stop()

  def on_subscribe(self, userdata, mid, granted_qos):
    if not self._on_subscribe_notified: # avoid SPAM
      self._on_subscribe_notified = True
      LOGGER.debug(f'Subscribed: {self.set_topic}')
  
  def on_connect(self, userdata, flags, rc):
    self.client.subscribe(self.set_topic, 2)
  
  def on_message(self, userdata, msg):
    LOGGER.debug(f'Received: {msg.topic}: {str(msg.payload)}')

class SendTextSubscriber(MqttSubscriber):

  def __init__(self, manager):
    super().__init__(manager, 'send_text')
  
  def on_message(self, userdata, msg):
    try:
      super().on_message(userdata, msg)
      if (msg.topic == self.set_topic):
        payload = json.loads(msg.payload)
        timeout = int(payload["timeout"])
        time_now = time.time()
        if (time_now > timeout):
          # mosquitto_pub -h localhost -p 1883 -t "mqtt_telegram_bot/send_text/set" -m "{\"timeout\": $(expr `date '+%s'` - 10), \"text\": \"sample\"}"
          LOGGER.info(f'Message ignored due to timeout')
        else:
          # mosquitto_pub -h localhost -p 1883 -t "mqtt_telegram_bot/send_text/set" -m "{\"timeout\": $(expr `date '+%s'` + 10), \"text\": \"sample\"}"
          manager.telegram_bot.send_text(payload["text"], payload.get('private', False))
    except:
      LOGGER.exception(f'Message handler failed')

class TelegramBot(Disposable):

  def __init__(self, manager):
    super().__init__('telegram_bot')
    self.manager = manager
    self._send_init_text()
  
  def send_text(self, text, private=False):
    try:
      if LOGGER.level <= logging.DEBUG:
        LOGGER.debug('Send text: ' + (text.replace("\n", "\\n") if not private else '<<private text>>'))
      base_url = CONFIG.TELEGRAM.API_URL
      chat_id = CONFIG.TELEGRAM.CHAT_ID
      params = {
        "chat_id": chat_id,
        "parse_mode": CONFIG.TELEGRAM.PARSE_MODE,
        "text": CONFIG.TELEGRAM.MESSAGE_PREFIX + text
      }
      req_url = f'{base_url}/sendMessage?{urllib.parse.urlencode(params)}'
      response = requests.get(req_url)
      return response
    except:
      LOGGER.exception("Failed to send text")
      return None
  
  def _send_init_text(self):
    self.send_text(CONFIG.TELEGRAM.MESSAGE_START)

  def _send_dispose_text(self):
    self.send_text(CONFIG.TELEGRAM.MESSAGE_STOP)

  def _dispose(self):
    self._send_dispose_text()

class Manager(Disposable):

  def __init__(self):
    super().__init__('manager')
    self._sensors = []
    self.add_sensor('running', True, False)
    self.telegram_bot = TelegramBot(self)
    self.send_text = SendTextSubscriber(self)

  def add_sensor(self, device_name, state, dispose_state=None):
    sensor = MqttSensor(self, device_name, state, dispose_state)
    self._sensors.append(sensor)
    return sensor
  
  def republish(self):
    if self._disposed: return
    for x in self._sensors: x.republish()

  def _dispose(self):
    pass
  
  def wait(self):
    #threading.Event().wait()
    while True:
      if self._disposed: return
      time.sleep(CONFIG.MQTT.REPUBLISH_INTERVAL)
      LOGGER.debug(f'Republish all')
      self.republish()

# main loop
try:
  manager = Manager()
  LOGGER.info(f'Started')
  manager.wait()

except KeyboardInterrupt:
  LOGGER.info("Exit event: Keyboard interrupt (ctrl+C)")
  exit_app()

except SigtermInterrupt:
  LOGGER.info("Exit event: Sigterm interrupt (kill)")
  exit_app()

except:
  LOGGER.exception("Exit event: Unhandled exception")
  exit_app(1)
