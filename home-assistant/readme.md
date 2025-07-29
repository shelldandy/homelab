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
- For USB devices (Zigbee/Z-Wave sticks), uncomment device mappings in docker-compose.yml
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