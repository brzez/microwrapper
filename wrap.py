import uasyncio as asyncio

device_name = None
wifi_connection = None


def _prefix_topic(topic, prefix=True):
    if prefix:
        return b'%s/%s' % (device_name, topic)
    return topic


def do_connect(ssid, password, tries=10):
    import network
    import time
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...', ssid)
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            tries -= 1
            time.sleep(1)
            if tries == 0:
                return None
    return sta_if.ifconfig()


def ensure_wifi(config):
    global wifi_connection
    wifi_connection = False
    if not wifi_connection and 'wifi_1' in config:
        wifi_connection = do_connect(**config.get('wifi_1'))
    if not wifi_connection and 'wifi_2' in config:
        wifi_connection = do_connect(**config.get('wifi_2'))


def get_device_id():
    import machine
    import ubinascii

    return ubinascii.hexlify(machine.unique_id())


subscribes = []
mqtt_client = None


def sub_cb(topic, msg):
    for sub_topic, f, prefix in subscribes:
        if topic == _prefix_topic(sub_topic, prefix):
            f(msg)


def publish(topic, message, prefix=True):
    global mqtt_client
    try:
        topic = _prefix_topic(topic, prefix)
        mqtt_client.publish(topic, message)
        return True
    except Exception as e:
        print(e)
        mqtt_client = None
        return False


def subscribe(topic, prefix=True):
    def _wrap(f):
        if isinstance(topic, str):
            t = topic.encode()
        else:
            t = topic
        if mqtt_client:
            try:
                mqtt_client.subscribe(_prefix_topic(t, prefix))
            except Exception as e:
                print('sub', e)
        subscribes.append((t, f, prefix))

    return _wrap


def ensure_mqtt(config):
    from umqttsimple import MQTTClient

    global mqtt_client
    if 'mqtt' not in config:
        return False
    mqtt_config = config['mqtt']

    mqtt_client = MQTTClient(get_device_id(),
                             mqtt_config.get('server'),
                             **mqtt_config.get('kwargs', {}))
    mqtt_client.set_callback(sub_cb)

    mqtt_client.connect()
    for (topic, f, prefix) in subscribes:
        print('MQTT sub to', topic)

        topic = _prefix_topic(topic, prefix)

        mqtt_client.subscribe(topic)


async def mqtt_tick(config):
    global mqtt_client

    while True:
        try:
            if mqtt_client:
                print('- checking messages')
                mqtt_client.check_msg()
            else:
                print('mqtt connect')
                ensure_mqtt(config)
        except Exception as e:
            print('mqtt', type(e), e)
            mqtt_client = None
        await asyncio.sleep_ms(30)


def get_heartbeat_message():
    return dict(device_name=device_name, connection=wifi_connection)


async def mqtt_heartbeat(config):
    if 'mqtt' not in config:
        return

    import ujson
    while True:
        publish(b'heartbeat', ujson.dumps(get_heartbeat_message()).encode(), False)
        await asyncio.sleep(10)


def boot(config):
    global device_name
    device_name = config.get('name', get_device_id().decode())
    ensure_wifi(config)
    ensure_mqtt(config)


async def tick(config):
    while True:
        ensure_wifi(config)
        await asyncio.sleep(5)


def wrap(fn, config_path):
    import ujson

    with open(config_path, 'r') as h:
        config = ujson.load(h)

    boot(config)
    loop = asyncio.get_event_loop()
    loop.create_task(fn())
    loop.create_task(tick(config))
    loop.create_task(mqtt_tick(config))
    loop.create_task(mqtt_heartbeat(config))
    loop.run_forever()
