"""Publish temper sensor data to MQTT."""

import argparse
import json
import logging
import socket
from datetime import datetime, timedelta

import temper
from slugify import slugify as slugify_base

from mqtt_base.mqtt_base import MQTTBaseApp
from mqtt_base.event import RefreshEvent
from mqtt_base.mqtt import MQTTConnectEvent

from .const import (
    APP_NAME,
    DEF_POLL_INTERVAL,
    DEF_REFRESH_INTERVAL,
    DEF_CHANGE_THRESHOLD,
    DEF_UNAVAILABLE_PAYLOAD,
    MIN_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(APP_NAME)


def slugify(text: str) -> str:
    """Slugify a string."""
    return slugify_base(text=text, separator="_")


class TemperdApp(MQTTBaseApp):
    APP_NAME = APP_NAME

    def __init__(self, args: dict):
        """Initialise TemperdApp class."""
        super().__init__(args)

        self.hostname = socket.gethostname()
        self.change_threshold: float = args["change_threshold"]
        self.poll_interval = timedelta(seconds=args["poll_interval"])
        self.unavailable_payload = args["unavailable_payload"]
        self.next_refresh = datetime.now()
        self.last_temp_ext = None
        self.tobj = None

    @classmethod
    def add_app_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=DEF_POLL_INTERVAL,
            help=f"Frequency of polling the temper device (minimum: {MIN_POLL_INTERVAL})",
        )
        parser.add_argument(
            "--change-threshold",
            type=float,
            default=DEF_CHANGE_THRESHOLD,
            help="Minimum change threshold for sending MQTT updates",
        )
        parser.add_argument(
            "--unavailable-payload",
            type=str,
            default=DEF_UNAVAILABLE_PAYLOAD,
            help="Payload to publish to topic if sensor is unavailable",
        )
        parser.set_defaults(refresh_interval=DEF_REFRESH_INTERVAL)

    def setup(self, args) -> None:
        """Set up temperd app."""
        _LOGGER.info("setting up %s", self.APP_NAME)
        _LOGGER.debug("args: %s", args)
        self.tobj = temper.Temper()

    def get_refresh_interval(self) -> float:
        """Determine time of next event."""
        return min(
            MIN_POLL_INTERVAL, self.poll_interval, self.next_refresh - datetime.now()
        )

    def get_mqtt_discovery_config(self, device_config: dict) -> dict:
        """Return MQTT discovery config."""

        entity_name = "temperature"
        entity_slug = slugify(entity_name)
        return {
            "binary_sensor": {
                entity_slug: {
                    # "device": device_data["device"],  ## exclude availability
                    "object_id": self.mqtt_discovery["object_id"],
                    "name": entity_name,
                    "icon": "mdi:thermometer",
                    "state_class": "measurement",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "state_topic": self.mqtt_topic,
                    "value_template": "{{ value_json['external']|default(None) }}",
                    "availability": {
                        "topic": self.mqtt_topic,
                        "value_template": "{{ 'online' if 'external' in value_json|default({ }) else 'offline' }}",
                    },
                    # "payload_on": self._payload_birth,
                    # "payload_off": self._payload_close,
                },
            },
        }

    def get_mqtt_device_config(self) -> dict:
        """Device config for Home Assistant MQTT discovery."""
        config = self.config
        device_data = {
            "identifiers": [APP_NAME + "_" + slugify(config.hostname)],
            "name": APP_NAME + " " + config.hostname,
        }

        # client_opts = mqtt_get_client_opts()
        # birth_msg = client_opts[OPT_BIRTH]
        # close_msg = client_opts[OPT_WILL]
        # # close_prefix = close_msg[OPT_MQTT_PREFIX]
        # # close_topic = close_msg[OPT_TOPIC]
        # ## NOTE: assumes MQTT close and birth topics are the same, and
        # ##       MQTT close and will payloads are the same
        # birth_topic = birth_msg[OPT_TOPIC]
        # birth_prefix = birth_msg[OPT_MQTT_PREFIX]
        # if birth_topic is not None:
        #     device_data["availability"] = [
        #         {
        #             "topic": self.mqtt_topic
        #             "payload_available": birth_msg[OPT_PAYLOAD],
        #             "payload_not_available": close_msg[OPT_PAYLOAD],
        #         },
        #     ]
        # return device_data

    def _publish_sensor(self, force: bool = False) -> bool:
        payload = None
        try:
            result = self.tobj.read()
            if not (type(result) is list and len(result) > 0):
                raise Exception
            try:
                cur_temp_int = float(result[0]["internal temperature"])
            except:
                cur_temp_int = None
            cur_temp_ext = float(result[0]["external temperature"])
            if (
                force
                or self.last_temp_ext is None
                or abs(self.last_temp_ext - cur_temp_ext) >= self.change_threshold
            ):
                payload = {"internal": cur_temp_int, "external": cur_temp_ext}
                self.last_temp_ext = cur_temp_ext
                self.publish_mqtt(
                    self.mqtt_topic,
                    json.dumps(payload),
                    self.mqtt_qos,
                    self.mqtt_retain,
                )
                self.next_refresh = datetime.now() + self.refresh_interval
                _LOGGER.debug("next refresh scheduled for %s", self.next_refresh)
                return True

            ## Sensor update skipped
            return False
        except:
            ## Sensor didn't return usable value, send unavailable payload
            self.publish_mqtt(
                self.mqtt_topic,
                self.unavailable_payload,
                self.mqtt_qos,
                self.mqtt_retain,
            )
            self.next_refresh = datetime.now() + self.refresh_interval
            return None

    def handle_event(self, event):
        """Handle temperd app event."""
        if isinstance(event, MQTTConnectEvent):
            self._publish_sensor(force=True)
        elif isinstance(event, RefreshEvent):
            force = datetime.now() >= self.next_refresh
            _LOGGER.debug("force = %s", force)
            self._publish_sensor(force=force)
        else:
            _LOGGER.error("unknown event type %s", type(event).__name__)


def main():
    TemperdApp.main()


if __name__ == "__main__":
    main()
