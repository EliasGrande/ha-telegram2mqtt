import json
import os
import ssl
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

BASE_TOPIC = os.environ.get('MQTT_BASE_TOPIC', 'mqtt_telegram_bot')
HOST = os.environ.get('MQTT_HOST', 'mosquitto')
PORT = int(os.environ.get('MQTT_PORT', '8883'))
USER = os.environ.get('MQTT_USER', 'mqtt')
PASSWORD = os.environ.get('MQTT_PASS', 'ExamplePassword123')
OUTPUT_FILE = os.environ.get('TELEGRAM_MOCK_OUTPUT', '/shared/telegram_messages.jsonl')

seen = {
    'available': False,
    'state': None,
}


def log(message):
    print(message, flush=True)


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(f'{BASE_TOPIC}/running/available', 1)
    client.subscribe(f'{BASE_TOPIC}/running/state', 1)


def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    if msg.topic.endswith('/available'):
        seen['available'] = payload == 'online'
    elif msg.topic.endswith('/state'):
        seen['state'] = payload


log('[1/4] Connecting verifier to MQTT broker...')
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id='verifier')
client.username_pw_set(USER, PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message
client.connect(HOST, PORT)
client.loop_start()

try:
    log('[2/4] Waiting for app availability topic...')
    deadline = time.time() + 60
    while time.time() < deadline and not seen['available']:
        time.sleep(1)

    if not seen['available']:
        raise SystemExit('App did not publish running availability in time')

    expired_payload = {
        'timeout': int(time.time()) - 10,
        'text': 'expired message',
        'private': False,
    }
    valid_payload = {
        'timeout': int(time.time()) + 30,
        'text': 'hello from verifier',
        'private': False,
    }

    log('[3/4] Publishing expired message (should be ignored)...')
    publish.single(
        topic=f'{BASE_TOPIC}/send_text/set',
        payload=json.dumps(expired_payload),
        qos=1,
        retain=False,
        hostname=HOST,
        port=PORT,
        auth={'username': USER, 'password': PASSWORD},
        tls={'insecure': True, 'cert_reqs': ssl.CERT_NONE},
    )

    log('[3/4] Publishing valid message (should reach Telegram mock)...')
    publish.single(
        topic=f'{BASE_TOPIC}/send_text/set',
        payload=json.dumps(valid_payload),
        qos=1,
        retain=False,
        hostname=HOST,
        port=PORT,
        auth={'username': USER, 'password': PASSWORD},
        tls={'insecure': True, 'cert_reqs': ssl.CERT_NONE},
    )

    messages_file = Path(OUTPUT_FILE)
    message_deadline = time.time() + 30
    log('[4/4] Waiting for Telegram mock confirmation...')
    while time.time() < message_deadline:
        if messages_file.exists():
            lines = [json.loads(line) for line in messages_file.read_text(encoding='utf-8').splitlines() if line.strip()]
            texts = []
            for line in lines:
                texts.extend(line.get('query', {}).get('text', []))
            if 'hello from verifier' in ''.join(texts) and 'expired message' not in ''.join(texts):
                log('TEST PASSED: availability, expired message handling, and Telegram delivery verified')
                raise SystemExit(0)
        time.sleep(1)

    raise SystemExit('Telegram mock did not receive the expected message in time')
finally:
    client.loop_stop()
    client.disconnect()
