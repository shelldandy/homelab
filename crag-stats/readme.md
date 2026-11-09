# Crag Stats

Private Crag Stats deployment at `https://cragstats.bowline.im`, protected by the existing Traefik `oidc-auth` middleware. It requires the external Docker network `frontend` (`docker network create frontend` if it does not already exist).

## Setup

1. Copy `.env.example` to `.env`.
2. Generate a session secret with `openssl rand -hex 32` and set `SESSION_SECRET`.
3. Optionally set `THECRAG_API_KEY` for scheduled logbook sync. Without it, import CSV exports from the app's Settings page. The API key can read private notes; never commit `.env`.
4. Start the app and worker:

   ```sh
   docker compose pull
   docker compose up -d
   ```

Check status and logs with `docker compose ps` and `docker compose logs -f`.

## Data and upgrades

The app and worker share `/mnt/docker-data/crag-stats`, with SQLite at `/mnt/docker-data/crag-stats/crag-stats.sqlite`. Keep both mounts pointed at the same directory. The containers are labeled to stop during `docker-volume-backup` backups.

Set `CRAG_STATS_IMAGE_TAG` in `.env` to pin a GHCR release instead of using `latest`. Upgrades preserve the database; Crag Stats applies migrations automatically on startup.
