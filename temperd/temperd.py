"""Publish temper sensor data to MQTT."""

import argparse
import json
import logging
from datetime import datetime, timedelta

import temper

from mqtt_base.mqtt_base import MQTTBaseApp
from mqtt_base.event import RefreshEvent
from mqtt_base.mqtt import MQTTConnectEvent

from .const import (
    APP_NAME,
    DEF_POLL_INTERVAL,
    DEF_REFRESH_INTERVAL,
    DEF_CHANGE_THRESHOLD,
    DEF_UNAVAILABLE_PAYLOAD,
)

_LOGGER = logging.getLogger(APP_NAME)


class TemperdApp(MQTTBaseApp):
    APP_NAME = APP_NAME

    def __init__(self, args: dict):
        """Initialise TemperdApp class."""
        super().__init__(args)

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
            help="Frequency of polling the temper device",
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
        return min(self.poll_interval, self.next_refresh - datetime.now())

    def handle_event(self, event):
        """Handle temperd app event."""

        def publish_sensor(force: bool = False) -> bool:
            payload = None
            result = self.tobj.read()
            if type(result) is list and len(result) > 0:
                try:
                    cur_temp_int = float(result[0]["internal temperature"])
                except:
                    cur_temp_int = None
                try:
                    cur_temp_ext = float(result[0]["external temperature"])
                    if (
                        force
                        or self.last_temp_ext is None
                        or abs(self.last_temp_ext - cur_temp_ext)
                        >= self.change_threshold
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
                        _LOGGER.debug(
                            "next refresh scheduled for %s", self.next_refresh
                        )
                        return True

                    ## Sensor update skipped
                    return False
                except:
                    pass

                ## Sensor didn't return usable value, send unavailable payload
                self.publish_mqtt(
                    self.mqtt_topic,
                    self.unavailable_payload,
                    self.mqtt_qos,
                    self.mqtt_retain,
                )

            return None

        if isinstance(event, MQTTConnectEvent):
            publish_sensor(force=True)
        elif isinstance(event, RefreshEvent):
            force = datetime.now() >= self.next_refresh
            _LOGGER.debug("force = %s", force)
            publish_sensor(force=force)
        else:
            _LOGGER.error("unknown event type %s", type(event).__name__)


def main():
    TemperdApp.main()


if __name__ == "__main__":
    main()
