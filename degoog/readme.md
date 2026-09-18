# Degoog

Self-hosted search aggregator at `search.bowline.im`. Queries multiple search
engines and merges the results, with support for custom engines, bang commands,
themes and plugins.

Upstream: https://github.com/degoog-org/degoog

## Services

- **degoog**: web UI + aggregator at `search.bowline.im` (container port 4444)

No database or cache container. Degoog uses an in-memory cache, which upstream
considers the right shape for a personal, low-traffic instance. Valkey (shared
cache) and Postgres can be added later without migrating existing data — see
`docker-compose-examples/` upstream.

## Security

The admin/store panel can install extensions, and **extensions run code on the
server**. Two independent gates are in place, and both matter:

1. **`oidc-auth`** — the Traefik plugin middleware. Nothing reaches the container
   without a Pocket ID session.
2. **`DEGOOG_SETTINGS_PASSWORD`** — gates the admin/store panel itself. Degoog
   reads it only from the environment; there is no UI or on-disk file for it.

Gate 2 is not redundant: a mistyped Traefik label silently drops gate 1, and
anything else on the `frontend` Docker network can reach port 4444 directly.

**Do not set `DEGOOG_PUBLIC_INSTANCE=true`.** Despite the name it is not an extra
lock — it is "anonymous visitor" mode. It replaces the settings page with a
cut-down version that has no Store tab, makes every server-side mutation API
return Unauthorized, and moves the admin panel to `/admin`. Setting it here made
the Store button dead. The password alone is the correct gate.

No `ports:` mapping is published — Traefik reaches the container over `frontend`.

## Setup

1. Copy `.env.example` to `.env` and fill in the values. Generate the password with:
   ```bash
   openssl rand -base64 32
   ```

2. Create the data directory. The image runs as `1000:1000` and will not create it:
   ```bash
   mkdir -p /mnt/docker-data/degoog
   ```
   If it ends up owned by another user, `sudo chown -R 1000:1000 /mnt/docker-data/degoog`.

3. Start it:
   ```bash
   make start-degoog
   ```

4. Visit `https://search.bowline.im`, log in via Pocket ID, and run a test query.
   Opening settings or the store prompts for `DEGOOG_SETTINGS_PASSWORD`.

## Notes

- No Pocket ID OIDC client is needed. Degoog has no native OIDC support; Traefik's
  `oidc-auth` middleware is the sole auth gate, the same as kiwix and pinchflat.
- Image is tracked at `:latest`. The project is young and moving fast, so pin to a
  release tag (e.g. `:0.26.0`) if an update ever breaks things.
- Search engines rate-limit datacenter IPs hard, so egress is deliberately direct
  rather than routed through Gluetun.
