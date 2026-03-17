# [Immich](https://github.com/immich-app/immich) + [iCloud Photos Downloader](https://github.com/boredazfcuk/docker-icloudpd)

Immich is a self-hosted photo and video management solution. The icloudpd containers download iCloud photos into directories that Immich mounts as external libraries.

## iCloud Photos Downloader

Configuration for icloudpd is in `.env.example.icloudpd`. Each user has their own env file (`.env.ignore.bowlinedandy`, `.env.ignore.susy`).

### MFA Initialization

If your Apple ID has multifactor authentication enabled, you need to initialize the cookie for each container:

```shell
docker exec -it bowlinedandy sync-icloud.sh --Initialise
docker exec -it susifluna sync-icloud.sh --Initialise
```

### Failsafe

Make sure to create a `.mounted` file inside of the `download_path` directory used in the env file.

## Library Scan Trigger

The `immich-library-scan` sidecar container automatically triggers Immich external library scans via the API so that photos downloaded by icloudpd are picked up without manual intervention.

### How it works

- Waits `INITIAL_DELAY` seconds (default: 1 hour) after startup
- Triggers a scan for each external library via `POST /api/libraries/{id}/scan`
- Sleeps `SCAN_INTERVAL` seconds (default: 24 hours), then repeats

### Setup

1. Generate an API key in Immich: Profile > Account Settings > API Keys (grant **Library** permissions)
2. Get library IDs: `curl -s http://localhost:2283/api/libraries -H "x-api-key: YOUR_KEY"`
3. Fill in the env vars in `.env`:
   - `IMMICH_API_KEY`
   - `IMMICH_LIBRARY_ID_BOWLINE`
   - `IMMICH_LIBRARY_ID_WIFE`
   - `SCAN_INTERVAL` (optional, default `86400`)
   - `INITIAL_DELAY` (optional, default `3600`)
