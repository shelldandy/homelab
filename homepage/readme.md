# Homepage

Dashboard for all homelab services at `https://www.bowline.im`, gated by the
Traefik `oidc-auth` plugin (Pocket ID).

## Config

`config/` is the versioned source of truth. The container reads its config from
`${CONFIG_PATH}` (`/mnt/docker-data/homepage`), like every other service, so it
is picked up by `backup-local`.

After editing anything in `config/`, sync it across:

```sh
cp config/*.yaml /mnt/docker-data/homepage/
```

Homepage hot-reloads YAML, so no restart is needed.

The container also generates `kubernetes.yaml`, `proxmox.yaml`, `custom.css`,
`custom.js` and `logs/` in `${CONFIG_PATH}` on startup. Those are runtime
artifacts and deliberately not tracked here.

## Notes

- `HOMEPAGE_ALLOWED_HOSTS` must match the Host rule or every request 400s. The
  container log prints the exact expected value.
- Homepage v2 has its own OIDC, left disabled: Traefik is the single auth gate,
  so enabling it would mean two redirects for the same identity.
- Icon names are verified against `homarr-labs/dashboard-icons`. `beets`,
  `pinchflat`, `soulseek` and `reactflux` have no icon there and use `mdi-`
  glyphs instead.
