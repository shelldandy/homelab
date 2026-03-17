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
