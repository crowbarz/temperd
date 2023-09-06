# temperd

Publish temper sensor data to MQTT.

## Installation

TODO

## Usage

```
usage: temperd [-h] [--poll-interval POLL_INTERVAL]
               [--change-threshold CHANGE_THRESHOLD] [-H HOST] [-P PORT]
               [--connect-timeout CONNECT_TIMEOUT]
               [--max-reconnect-delay MAX_RECONNECT_DELAY] [-u USERNAME]
               [-p PASSWORD] [--password-file PASSWORD_FILE] [-c CLIENT_ID] [-C] -t
               TOPIC [-q {0,1,2}] [-R] [--keepalive KEEPALIVE] [--tls]
               [--tls-insecure TLS_INSECURE] [--ca-certs CA_CERTS]
               [--certfile CERTFILE] [--keyfile KEYFILE]
               [--birth-topic BIRTH_TOPIC] [--birth-payload BIRTH_PAYLOAD]
               [--birth-qos {0,1,2}] [--birth-retain] [--will-topic WILL_TOPIC]
               [--will-payload WILL_PAYLOAD] [--will-qos {0,1,2}] [--will-retain]
               [--refresh-interval REFRESH_INTERVAL] [--daemon] [--pidfile PIDFILE]
               [-d DEBUG] [--logfile LOGFILE] [-v]

options:
  -h, --help            show this help message and exit
  --poll-interval POLL_INTERVAL
                        Frequency of polling the temper device
  --change-threshold CHANGE_THRESHOLD
                        Minimum change threshold for sending MQTT updates
```
