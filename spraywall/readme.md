# Spraywall

Spray-wall route-setting PWA with AI hold detection, backed by Postgres + MinIO with Pocket ID SSO.
Upstream: https://github.com/shelldandy/spraywall

## Services

- **web**: nginx frontend at `muro.bowline.im` (proxies the API)
- **server**: Go API (runs migrations and creates the MinIO bucket on start)
- **worker**: Python YOLOv8 hold detection (CPU only)
- **postgres** / **minio**: database and image storage

## Setup

1. Copy `.env.example` to `.env`, generate the secrets (`openssl rand -hex 32`) for
   `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD` and `JWT_SECRET`.

2. Create the data directory: `sudo mkdir -p /mnt/docker-data/spraywall` (owned by your user).

3. Create a Pocket ID OIDC client:
   - Callback URL: `https://muro.bowline.im/api/auth/oidc/callback`
   - Put the client ID/secret into `SPRAYWALL_OIDC_CLIENT_ID` / `SPRAYWALL_OIDC_CLIENT_SECRET`
   - Members of the Pocket ID group named by `SPRAYWALL_OIDC_ADMIN_GROUP` become instance admins
     (admin rights lapse 24h after the last SSO login).

4. Start:

   ```bash
   docker compose up -d
   ```

5. Visit `https://muro.bowline.im` and use the "Pocket ID" button.

## Notes

- `PASSWORD_LOGIN_ENABLED=true` keeps local login as a fallback. Set it to `false` for SSO-only.
- Linking an existing password account to SSO (matching verified email) removes its password.
- Update with `docker compose pull && docker compose up -d`.
