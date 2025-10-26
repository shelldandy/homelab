# Home Assistant

Home Assistant is an open-source home automation platform that focuses on privacy and local control.

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

3. Start the service:
   ```bash
   docker compose up -d
   ```

## Access

- **External**: https://homeassistant.${DOMAIN}
- **Local**: http://localhost:8123

## Configuration

### Initial Setup
1. Access Home Assistant via browser
2. Complete the onboarding wizard
3. Create admin account
4. Configure location and units

### Device Integration

#### Z-Wave (Connect ZWA-2)
The Home Assistant Connect ZWA-2 Z-Wave controller is integrated via the Z-Wave JS UI service.

**Setup Steps:**
1. Z-Wave JS UI is already configured in docker-compose.yml and will start automatically
2. Access Z-Wave JS UI web interface:
   - Local: http://localhost:8091
   - External: https://zwave.${DOMAIN}
3. Configure Z-Wave JS UI:
   - Go to **Settings → Z-Wave**
   - Set **Serial Port** to `/dev/zwave`
   - Click **Save**
4. Generate Security Keys (Settings → Z-Wave → Security Keys):
   - Click **Generate** for each key type (S0, S2 Access Control, S2 Authenticated, S2 Unauthenticated)
   - **IMPORTANT**: Save these keys securely - you'll need them to re-pair devices if you rebuild the container
5. Set RF Region (Settings → Z-Wave → RF Manager):
   - Set **RF Region** to your location (USA, EU, ANZ, etc.)
   - Click **Save**
6. Verify controller status in dashboard shows **Ready** and **Active**
7. Enable WebSocket Server (Settings → Home Assistant):
   - Enable **WS Server**
   - Note the URL: `ws://zwave-js-ui:3000`
8. Add Z-Wave JS integration in Home Assistant:
   - Go to **Settings → Devices & Services**
   - Click **Add Integration**
   - Search for and select **Z-Wave JS**
   - Enter WebSocket URL: `ws://zwave-js-ui:3000`
   - Click **Submit**

**Pairing Z-Wave Devices:**
1. In Z-Wave JS UI, click **Control Panel**
2. Click **Add Node** (or **Include**)
3. Follow your device's pairing instructions (usually triple-press a button)
4. Device will appear in both Z-Wave JS UI and Home Assistant

**Backup:**
- Security keys and network config are stored in `${CONFIG_PATH}/zwave-js-ui`
- Export security keys: Settings → Z-Wave → Security Keys (save as JSON)

#### Other USB Devices
- For Zigbee sticks or other USB devices, uncomment device mappings in docker-compose.yml
- Restart container after device changes: `docker compose restart homeassistant`

### Authentication (Optional)
To enable OIDC authentication for external access:
1. Configure a new application in Pocket ID
2. Uncomment the OIDC middleware line in docker-compose.yml
3. Restart the service

### Backup
Configuration is stored in `${CONFIG_PATH}/home-assistant/config`
Backups are stored in `${CONFIG_PATH}/home-assistant/backups`

## Networking

- **Frontend Network**: Traefik reverse proxy access
- **Backend Network**: Internal service communication for IoT devices
- **Port 8123**: Direct local access for device discovery and mobile apps

## Integrations

Home Assistant can integrate with many services in your homelab:
- **AdGuard**: DNS filtering and network monitoring
- **Grafana**: System monitoring and dashboards
- **MQTT**: IoT device communication
- **Jellyfin**: Media control and status

## Troubleshooting

- Check container logs: `docker compose logs -f homeassistant`
- Verify network connectivity: `docker compose exec homeassistant ping google.com`
- Check configuration: Configuration > Check Configuration in Home Assistant
- Restart service: `docker compose restart homeassistant`