#!/usr/bin/python
# -*- coding: UTF-8 -*-
# created: 20.06.2018
# author:  TOS

import logging
import time
import os
import json

from paho.mqtt import client
from docker import get_secret
import rpistatus

app_name = 'RPI-Status'
logging_interval = 5  # seconds

mqtt_server = "core-mosquitto"
mqtt_port = 1883
mqtt_pw = "xxx"
mqtt_user = "davidfreina"

topic = "homeassistant/{component}/{nodeid}/{objectid}/config"
availTopic = "davidfreina/rpi/state"
stateTopic = "davidfreina/rpi/{}"


def connect_mqtt(logger):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker")
        else:
            logger.info("Could not connect to MQTT Broker")

    mqttclient = client.Client(rpistatus.hostname())
    mqttclient.username_pw_set(mqtt_user, mqtt_pw)
    mqttclient.on_connect = on_connect

    mqttclient.connect(mqtt_server, mqtt_port)

    return mqttclient


def scaling(val, factor):
    return round(val / factor, 2)


def publish_mqtt(subtopic, measurements, divisor, data, unit, deviceclass):
    if divisor != 0:
        data = {k: scaling(v, divisor) for k, v in data.items()}
    if deviceclass != "":
        deviceclass = '{"device_class": "' + deviceclass + '",'
    else:
        deviceclass = '{'
    mqttclient.publish(topic=stateTopic.format(subtopic),
                       payload=json.dumps(data), qos=0, retain=True)
    for measurement in measurements:
        log.info("publish to topic '{}': {}".format(topic.format(
            component="sensor", nodeid=subtopic, objectid=measurement), data.get(measurement)))
        payload = deviceclass + '"availability_topic": "' + availTopic + '","device": {"identifiers": ["rpi_' + subtopic + '"],"manufacturer": "Raspberry Pi Foundation","model": "Raspberry Pi 4 B","name": "' + subtopic + '","sw_version": "0.0.1"},"name": "RPi: ' + subtopic + ' ' + measurement + \
            '","state_class": "measurement","state_topic": "davidfreina/rpi/' + subtopic + '","json_attributes_topic": "davidfreina/rpi/' + subtopic + \
            '","unique_id": "rpi_' + subtopic + '_' + measurement + '","unit_of_measurement": "' + \
            unit + \
            '","value_template": "{{ value_json.' + measurement + ' }}"}'
        mqttclient.publish(topic=topic.format(component="sensor", nodeid=subtopic,
                                              objectid=measurement), payload=payload, qos=0, retain=True)


if __name__ == '__main__':

    log = logging.getLogger(app_name)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s:%(levelname)s:%(message)s")

    log.info("Start {} logging...".format(app_name))

    mqttclient = connect_mqtt(log)

    status_topic = 'davidfreina/rpi/state'
    mqttclient.will_set(status_topic, qos=0, payload='offline', retain=True)
    mqttclient.publish(topic=status_topic,
                       payload='online', qos=0, retain=True)

    hostname = rpistatus.hostname()

    while True:
        t0 = time.time()

        for subtopic in ['clock', 'voltage', 'temperature']:
            data = getattr(rpistatus, subtopic)()
            if(subtopic == "clock"):
                publish_mqtt(subtopic, ['arm', 'core', 'h264', 'isp', 'v3d', 'uart', 'pwm',
                                        'emmc', 'pixel', 'vec', 'hdmi', 'dpi'], 1000000000, data, "GHz", "")
            elif(subtopic == "voltage"):
                publish_mqtt(
                    subtopic, ['core', 'sdram_c', 'sdram_i', 'sdram_p'], 0, data, "V", "voltage")
            elif(subtopic == "temperature"):
                publish_mqtt(subtopic, ['core'], 0, data, "°C", "temperature")

        mqttclient.publish(topic=status_topic,
                           payload='online', qos=0, retain=True)

        while (time.time()-t0) < logging_interval:
            time.sleep(0.1)

    log.info("Stop logging...")
