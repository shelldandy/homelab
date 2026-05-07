# [Kiwix](https://kiwix.org/)

Offline knowledge base. Serves ZIM files via a web interface.

Download ZIM files from [kiwix.org](https://download.kiwix.org/zim/) and place them in the path configured by `ZIM_PATH`.

## Access

| Method        | URL                        | Auth |
| ------------- | -------------------------- | ---- |
| Traefik       | `https://kiwix.bowline.im` | OIDC |
| LAN (offline) | `http://<host-ip>:9999`    | None |

Port 9999 is exposed for offline use when internet (and therefore OIDC) is unavailable. Remove the `ports:` section from `docker-compose.yml` if you don't need unauthenticated LAN access.

## Notes

- The kiwix-serve image runs as a non-root user by default. No `user:` directive is needed.
- ZIM files must be readable by the container's default user. Check permissions if kiwix fails to start.
