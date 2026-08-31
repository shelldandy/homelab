# Vaultwarden

Vaultwarden is a lightweight, self-hosted implementation of the Bitwarden server API written in Rust. It's compatible with all official Bitwarden clients and provides a secure password management solution.

## Features

- Full compatibility with official Bitwarden clients
- Lightweight and fast (written in Rust)
- Supports organizations, attachments, and most Bitwarden features
- Web interface for administration
- SQLite or PostgreSQL database support
- HTTPS/TLS encryption via Traefik

## Setup

### Prerequisites

- Ensure external networks are created:
  ```bash
  docker network create frontend
  docker network create backend
  ```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your configuration:
   - Set `SUBDOMAIN` to your desired subdomain (e.g., `vaultwarden`)
   - Set `CONFIG_PATH` to your data storage path
   - Generate `ADMIN_TOKEN` with: `docker exec -it vaultwarden /vaultwarden hash`
   - Configure database credentials
   - Adjust other settings as needed

### Database Options

**PostgreSQL (Recommended for Production):**
- Uses the included PostgreSQL container
- Better performance for multiple users
- Requires database credentials in `.env`

**SQLite (Simpler Setup):**
- Remove the `db` service from `docker-compose.yml`
- Comment out `DATABASE_URL` environment variable
- Data stored in SQLite file within the data volume

### Deploy

```bash
# Start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

## Access

- **Web Interface**: `https://vault.bowline.im`
- **Admin Panel**: `https://vault.bowline.im/admin` (requires ADMIN_TOKEN)

## Security Considerations

### Essential Security Settings

1. **Disable Public Signups**: Set `SIGNUPS_ALLOWED=false` in production
2. **Strong Admin Token**: Generate with `docker exec -it vaultwarden /vaultwarden hash`
3. **Regular Backups**: Backup your data directory and database regularly
4. **HTTPS Only**: Ensure Traefik is properly configured with SSL certificates

### User Registration

With `SIGNUPS_ALLOWED=false`, new users must be invited:
1. Access admin panel: `https://vault.bowline.im/admin`
2. Enter your admin token
3. Use "Invite User" to send registration invitations

### Backup Strategy

```bash
# Backup data directory
tar -czf vaultwarden-backup-$(date +%Y%m%d).tar.gz /path/to/config/data

# Backup PostgreSQL database (if using)
docker compose exec db pg_dump -U vaultwarden vaultwarden > vaultwarden-db-backup-$(date +%Y%m%d).sql
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBDOMAIN` | Subdomain for the service | `vaultwarden` |
| `CONFIG_PATH` | Path to store configuration and data | - |
| `ADMIN_TOKEN` | Token for admin panel access | - |
| `SIGNUPS_ALLOWED` | Allow new user registration | `false` |
| `LOG_LEVEL` | Logging level | `warn` |
| `POSTGRES_DB` | Database name | `vaultwarden` |
| `POSTGRES_USER` | Database username | `vaultwarden` |
| `POSTGRES_PASSWORD` | Database password | - |

## Client Configuration

### Official Bitwarden Clients

Configure any official Bitwarden client to use your self-hosted instance:

1. **Server URL**: `https://vault.bowline.im`
2. Create an account (if signups enabled) or use admin invitation
3. Install official Bitwarden apps on your devices
4. Sign in with your server URL and credentials

### Supported Clients

- Web Vault (built-in)
- Browser Extensions (Chrome, Firefox, Safari, Edge)
- Desktop Applications (Windows, macOS, Linux)
- Mobile Apps (iOS, Android)
- CLI tool (see [Command Line Interface](#command-line-interface))

## Command Line Interface

The `vaultwarden-cli` container runs the official Bitwarden CLI (`bw`) against
this instance. It talks to the server directly over the `backend` network at
`http://vaultwarden:80`, so it does not depend on Traefik, public DNS, or the
certificate being valid.

The CLI is installed via `npm` when the container starts, so the first boot
takes a few seconds and requires outbound internet access. State (server
config, login) persists in `${CONFIG_PATH}/cli`, so a restart does not force
you to log in again.

### Usage

```bash
# One time: log in (prompts for password, and 2FA if enabled)
docker exec -it vaultwarden-cli bw login <your-email>

# Unlock to get a session key, then pass it to each command
export BW_SESSION=$(docker exec -it vaultwarden-cli bw unlock --raw)

docker exec -it -e BW_SESSION="$BW_SESSION" vaultwarden-cli bw list items
docker exec -it -e BW_SESSION="$BW_SESSION" vaultwarden-cli bw get password github
docker exec -it -e BW_SESSION="$BW_SESSION" vaultwarden-cli bw sync

# Lock when you are done
docker exec -it vaultwarden-cli bw lock
```

Anything written to `/export` inside the container lands in
`${CONFIG_PATH}/cli/export` on the host.

### Session key handling

`BW_SESSION` is a decryption key for the entire vault. Treat it like the master
password:

- Do not write it to a file, a `.env`, or anywhere it gets committed.
- Prefer `export BW_SESSION=$(...)` over pasting it inline, so it does not sit
  in shell history.
- Run `bw lock` when finished, and `unset BW_SESSION`.
- Note that `bw export` produces a **plaintext** vault dump unless you pass
  `--format encrypted_json`.

## Troubleshooting

### Common Issues

1. **Cannot access admin panel**:
   - Verify `ADMIN_TOKEN` is set correctly
   - Check container logs: `docker compose logs vaultwarden`

2. **Database connection errors**:
   - Verify database credentials in `.env`
   - Ensure database container is running: `docker compose ps`

3. **Certificate/TLS issues**:
   - Verify Traefik is running and configured
   - Check domain DNS resolution
   - Review Traefik logs

4. **CLI container restarting or `bw` not found**:
   - The CLI is installed at startup; check `docker compose logs vaultwarden-cli`
     for npm failures (usually no outbound network)
   - Confirm the server URL with `docker exec -it vaultwarden-cli bw status`

### Logs

```bash
# Container logs
docker compose logs -f vaultwarden

# Application logs (if LOG_FILE is configured)
docker compose exec vaultwarden tail -f /data/vaultwarden.log
```

## Future Enhancements

### OIDC/SSO Integration

For SSO integration with Pocket ID, consider using the OIDCWarden fork:
- Repository: https://github.com/Timshel/OIDCWarden
- Provides OIDC authentication support
- Requires additional configuration for SSO providers

## Links

- [Official Vaultwarden Repository](https://github.com/dani-garcia/vaultwarden)
- [Vaultwarden Documentation](https://github.com/dani-garcia/vaultwarden/wiki)
- [Bitwarden Official Site](https://bitwarden.com/)
- [Docker Hub - Vaultwarden](https://hub.docker.com/r/vaultwarden/server)