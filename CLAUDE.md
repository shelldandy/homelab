# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Docker Compose-based homelab setup for self-hosted services. Each service is organized in its own directory with a docker-compose.yml file and associated configuration.

## Architecture

### Network Architecture
- **frontend**: External Docker network for services accessible via Traefik reverse proxy
- **backend**: External Docker network for internal service communication
- **arr_network**: Internal network for Arr stack services (Sonarr, Radarr, Prowlarr, etc.)
- **authentik_network**: Internal network for Authentik authentication services

### Core Infrastructure
- **Traefik**: Reverse proxy with Cloudflare DNS challenge for HTTPS certificates
- **Authentik**: Identity provider and SSO
- **TinyAuth**: Forward auth middleware for Traefik
- **Watchtower**: Automatic container updates

## Common Commands

### Network Setup
Before starting any services, create the required external networks:
```bash
docker network create frontend
docker network create backend
```

### Service Management
```bash
# Start a service
cd <service-directory>
docker compose up -d

# View logs
docker compose logs -f

# Update service
docker compose pull && docker compose up -d

# Stop service
docker compose down

# Rebuild and restart
docker compose down && docker compose up -d --build
```

### Volume Migration
To migrate from named volumes to bind mounts:
```bash
docker-compose down
# Add volume-copier service to docker-compose.yml
docker-compose run --rm volume-copier
# Update volume paths in service configuration
```

### Configuration
- Environment variables are stored in `.env` files in each service directory
- Example configurations are provided as `.env.example` files
- Configuration paths typically use `${CONFIG_PATH}` or `${BASE_PATH}` variables
- Media shares are mounted at `${MEDIA_SHARE}:/share`

## Service Categories

### Media Management (Arr Stack)
- **Sonarr**: TV show management
- **Radarr**: Movie management (includes separate mmarr instance)
- **Readarr**: Book management
- **Lidarr**: Music management
- **Prowlarr**: Indexer management
- **Bazarr**: Subtitle management
- **qBittorrent**: Torrent client (VPN-protected via Gluetun)

### Media Streaming
- **Jellyfin**: Media server
- **Navidrome**: Music streaming
- **Immich**: Photo management

### Authentication & Security
- **Authentik**: Identity provider
- **TinyAuth**: Forward auth for Traefik
- **AdGuard**: DNS filtering

### Development & Productivity
- **Forgejo**: Git hosting
- **Woodpecker**: CI/CD
- **Docmost**: Documentation
- **Hoarder**: Bookmark management

## Environment Variables

Most services use common environment variables:
- `PUID`/`PGID`: User/group IDs for LinuxServer containers
- `TZ`: Timezone
- `DOMAIN`: Primary domain name
- `CONFIG_PATH`: Base path for configuration storage
- `MEDIA_SHARE`: Path to media storage

## VPN Configuration

qBittorrent runs through Gluetun VPN container:
- Uses `network_mode: "service:gluetun"`
- Port forwarding managed by GSP mod
- VPN providers configured via environment variables

## Traefik Labels

Services use consistent Traefik labeling:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.{service}.rule=Host(`{service}.{domain}`)"
  - "traefik.http.services.{service}.loadbalancer.server.port={port}"
  - "traefik.http.routers.{service}.middlewares=tinyauth"  # For protected services
```