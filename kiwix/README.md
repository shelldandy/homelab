# [Kiwix](https://kiwix.org/)

Offline knowledge base. Serves ZIM files via a web interface.

Download ZIM files from [kiwix.org](https://download.kiwix.org/zim/) and place them in the path configured by `ZIM_PATH`.

## Access

| Method        | URL                        | Auth |
| ------------- | -------------------------- | ---- |
| Traefik       | `https://kiwix.bowline.im` | OIDC |
| LAN (offline) | `http://<host-ip>:9999`    | None |

Port 9999 is exposed for offline use when internet (and therefore OIDC) is unavailable. Remove the `ports:` section from `docker-compose.yml` if you don't need unauthenticated LAN access.

## Downloading ZIM files

Browse available files at [download.kiwix.org/zim/](https://download.kiwix.org/zim/), then download with:

```bash
docker compose run --rm zim-downloader <URL>
```

For example:

```bash
docker compose run --rm zim-downloader https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi_2024-01.zim
```

The downloader uses [aria2](https://aria2.github.io/) with 16 parallel connections for fast downloads. Runs as UID 1000 to match host directory ownership; kiwix-serve (UID 1001) reads the files via world-readable permissions.

For automated updates of existing ZIM files, see [kiwix-zim-updater](https://github.com/jojo2357/kiwix-zim-updater).

## Notes

- The kiwix-serve image runs as a non-root user by default. No `user:` directive is needed.
- ZIM files must be readable by the container's default user. Check permissions if kiwix fails to start.
