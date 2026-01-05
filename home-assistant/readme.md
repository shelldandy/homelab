# Home Assistant

Home Assistant is an open-source home automation platform that focuses on privacy and local control.

## Services

| Service           | Description                          | Port         | URL                     |
| ----------------- | ------------------------------------ | ------------ | ----------------------- |
| **homeassistant** | Core home automation platform        | 8123         | `ha.${DOMAIN}`          |
| **matter-server** | Matter/Thread device support         | host network | -                       |
| **mosquitto**     | MQTT broker for IoT devices          | 1883         | -                       |
| **zigbee2mqtt**   | Zigbee device management via SLZB-06 | 8124         | `zigbee2mqtt.${DOMAIN}` |

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

| Service        | External                        | Local                   |
| -------------- | ------------------------------- | ----------------------- |
| Home Assistant | `https://ha.${DOMAIN}`          | `http://localhost:8123` |
| Zigbee2MQTT    | `https://zigbee2mqtt.${DOMAIN}` | `http://localhost:8124` |
| MQTT           | -                               | `localhost:1883`        |

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

| Service                | Path                                    |
| ---------------------- | --------------------------------------- |
| Home Assistant config  | `${CONFIG_PATH}/home-assistant/config`  |
| Home Assistant backups | `${CONFIG_PATH}/home-assistant/backups` |
| Matter server          | `${CONFIG_PATH}/matter-server/data`     |
| Mosquitto data         | `${CONFIG_PATH}/mosquitto/data`         |
| Zigbee2MQTT data       | `${CONFIG_PATH}/zigbee2mqtt/data`       |

## Scene Presets Cycling

The [hass-scene_presets](https://github.com/Hypfer/hass-scene_presets) integration allows cycling through color presets for light groups. To add a new scene cycling automation:

### 1. Add input_select to configuration.yaml

```yaml
input_select:
  your_light_scene:
    name: "Your Light Scene"
    options:
      - "Rest"
      - "Relax"
      - "Bright"
    initial: "Rest"
    icon: mdi:lightbulb-group
```

### 2. Add cycle script to includes/scripts.yaml

```yaml
cycle_your_light_scene:
  alias: "Cycle Your Light Scene"
  sequence:
    - service: input_select.select_next
      target:
        entity_id: input_select.your_light_scene
      data:
        cycle: true
```

### 3. Add automation to includes/automations.yaml

```yaml
- alias: "Apply Your Light Scene Preset"
  trigger:
    - platform: state
      entity_id: input_select.your_light_scene
  action:
    - variables:
        preset_map:
          Rest: "e03267e7-9914-4f47-97fe-63c0bd317fe7"
          Relax: "e71b2ef3-1b15-4c4b-b036-4b3d6efe58f8"
          Bright: "84ebc26c-9d61-4d25-830c-41ea66f1c325"
    - service: scene_presets.apply_preset
      data:
        preset_id: "{{ preset_map[trigger.to_state.state] }}"
        targets:
          entity_id: light.your_light_entity
        brightness: 150
        transition: 1
  mode: single
```

### 4. Reload configuration

- Go to Developer Tools > YAML
- Click "Input selects", "Scripts", and "Automations" reload buttons
- Or restart Home Assistant

### Common Preset IDs

| Preset       | UUID                                 |
| ------------ | ------------------------------------ |
| Rest         | e03267e7-9914-4f47-97fe-63c0bd317fe7 |
| Relax        | e71b2ef3-1b15-4c4b-b036-4b3d6efe58f8 |
| Read         | 035b6ecf-414e-4781-abc7-3911556097cb |
| Bright       | 84ebc26c-9d61-4d25-830c-41ea66f1c325 |
| Dimmed       | 8f55e62a-e5f8-456a-9e8b-61f314bd4e99 |
| Concentrate  | 0cbec4e8-d064-4457-986a-fe6078a63f39 |
| Energize     | 0eeacfc5-2d81-4035-a23d-4a9bc02af965 |
| Nightlight   | b6f58e22-677f-4670-8677-3dea4ac60383 |
| Warm embrace | 73b2c0b3-b4c5-4307-8873-eb231c83e996 |
| Motown       | 7dded6f8-a2aa-4726-b391-21e9a0f76eee |
| Tokyo        | de7eda64-84bf-4ed6-a4fa-76e0ebdd1968 |
| Miami        | a592fa63-4ba6-4399-a120-1c0b79ac832d |
| Galaxy       | a6ba3a6e-1e3a-41fd-84f2-f7b021935deb |
| Moonlight    | a87a8467-82ff-43f8-aaf3-6649b57b1480 |

<https://github.com/Hypfer/hass-scene_presets/blob/master/custom_components/scene_presets/assets/Readme.md>

To get all preset IDs, run:

```bash
docker compose exec homeassistant cat /config/custom_components/scene_presets/presets.json | \
  python3 -c "import sys, json; d=json.load(sys.stdin); [print(f'{p[\"name\"]}: {p[\"id\"]}') for p in d['presets']]"
```

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
