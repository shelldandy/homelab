# Home Assistant

Home Assistant is an open-source home automation platform that focuses on privacy and local control.

## Services

| Service | Description | Port | URL |
|---------|-------------|------|-----|
| **homeassistant** | Core home automation platform | 8123 | `ha.${DOMAIN}` |
| **matter-server** | Matter/Thread device support | host network | - |
| **mosquitto** | MQTT broker for IoT devices | 1883 | - |
| **zigbee2mqtt** | Zigbee device management via SLZB-06 | 8124 | `zigbee2mqtt.${DOMAIN}` |

## Files

```
home-assistant/
├── docker-compose.yml              # Service definitions
├── .env                            # Environment variables (not committed)
├── .env.example                    # Example environment variables
├── configuration.yaml              # Home Assistant config (version controlled)
├── includes/                       # Additional HA config files
├── mosquitto.conf                  # MQTT broker configuration
└── zigbee2mqtt-configuration.yaml  # Zigbee2MQTT configuration
```

## Setup

1. Copy the environment file and configure it:
   ```bash
   cp .env.example .env
   # Edit .env with your specific values
   ```

2. Ensure required networks exist:
   ```bash
   docker network create frontend
   docker network create backend
   ```

3. Start all services:
   ```bash
   docker compose up -d
   ```

## Access

| Service | External | Local |
|---------|----------|-------|
| Home Assistant | `https://ha.${DOMAIN}` | `http://localhost:8123` |
| Zigbee2MQTT | `https://zigbee2mqtt.${DOMAIN}` | `http://localhost:8124` |
| MQTT | - | `localhost:1883` |

## Zigbee Setup (SLZB-06)

The Zigbee network uses an SLZB-06 network coordinator:

1. Configure the SLZB-06 at `http://<slzb-ip>/` and set it to **Coordinator mode**
2. Update the IP address in `zigbee2mqtt-configuration.yaml`
3. In Home Assistant, add the MQTT integration:
   - Settings → Devices & Services → Add Integration → MQTT
   - Broker: `mosquitto` (or `localhost` if accessing from host)
   - Port: `1883`

Zigbee devices will auto-discover in Home Assistant via MQTT.

## Data Storage

| Service | Path |
|---------|------|
| Home Assistant config | `${CONFIG_PATH}/home-assistant/config` |
| Home Assistant backups | `${CONFIG_PATH}/home-assistant/backups` |
| Matter server | `${CONFIG_PATH}/matter-server/data` |
| Mosquitto data | `${CONFIG_PATH}/mosquitto/data` |
| Zigbee2MQTT data | `${CONFIG_PATH}/zigbee2mqtt/data` |

## Troubleshooting

```bash
# Check all service logs
docker compose logs -f

# Check specific service
docker compose logs -f zigbee2mqtt
docker compose logs -f mosquitto

# Restart a service
docker compose restart zigbee2mqtt

# Verify MQTT connectivity
docker compose exec mosquitto mosquitto_sub -t '#' -v
```