# [Immich](https://github.com/immich-app/immich) + [iCloud Photos Downloader](https://github.com/boredazfcuk/docker-icloudpd)

Immich is a self-hosted photo and video management solution. The icloudpd containers download iCloud photos into directories that Immich mounts as external libraries.

## iCloud Photos Downloader

Configuration for icloudpd is in `.env.example.icloudpd`. Each user has their own env file (`.env.ignore.bowlinedandy`, `.env.ignore.susy`).

### MFA Initialization

If your Apple ID has multifactor authentication enabled, you need to initialize the cookie for each container:

```shell
make init-bowlinedandy
make init-susifluna
# or both:
make init-all
```

> **2FA code not arriving on device?** On iOS 18+ Apple removed the manual "Get Verification Code" option. Turn on **Airplane Mode**, then go to **Settings > [your name] > Sign-In & Security** to generate a verification code locally. See [boredazfcuk/docker-icloudpd#933](https://github.com/boredazfcuk/docker-icloudpd/issues/933).

### Updating Telegram Bot Token

The `boredazfcuk/icloudpd` container reads its runtime config from `icloudpd.conf` (persisted in the config bind mount), **not** from the env file after initial setup. If you rotate the Telegram bot token:

1. Update the token in the env files (`.env.ignore.bowlinedandy`, `.env.ignore.susy`)
2. Update the token in **both** conf files:
   - `data/icloudpd/config/bowlinedandy/icloudpd.conf`
   - `data/icloudpd/config/susifluna/icloudpd.conf`
3. Restart the containers: `docker compose restart bowlinedandy susifluna`

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
