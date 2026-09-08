# Jellyfin 10.11.11 → 12.0 Upgrade: Research & Blockers

**Date:** September 8, 2026
**Status:** Deferred — waiting for a 12.0.x point release and stable plugin builds
**Severity:** N/A — planned maintenance, no outage
**Current version:** `lscr.io/linuxserver/jellyfin:10.11.11`

## Summary

Jellyfin 12.0 released on 2026-09-08 (version numbering skipped from 10.11 straight to 12.0). LinuxServer published `12.0ubu2604-ls48` the same day. Investigated upgrading and **decided to wait**: it is a day-one major release with a **one-way, irreversible database migration**, and 4 of our 9 users authenticate exclusively through a plugin whose upstream repository has been archived.

The image bump itself is one line. Everything below is why that one line is not the hard part.

## Current State (verified on the host, 2026-09-08)

| Fact             | Value                                                                                                      |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| Running image    | `lscr.io/linuxserver/jellyfin:10.11.11` (`10.11.11ubu2404-ls41`)                                           |
| Live database    | `/mnt/docker-data/jellyfin/config/data/data/jellyfin.db` — **486 MB**                                      |
| Config dir total | `/mnt/docker-data/jellyfin/config` — **15 GB**                                                             |
| Free space       | 734 G available on `/mnt/docker-data`                                                                      |
| Users            | 9                                                                                                          |
| GPU transcoding  | AMD Radeon 780M — `DOCKER_MODS=linuxserver/mods:jellyfin-amd`, `/dev/kfd` + `/dev/dri`, `group_add: video` |

### Gotcha: there are two `jellyfin.db` files

`config/data/jellyfin.db` and `config/data/library.db` are dated **Dec 2024** and are **stale leftovers** from the pre-10.11 layout. The live database is one directory deeper:

```
config/data/data/jellyfin.db      486 MB   ← live, modified today
config/data/jellyfin.db           724 KB   ← stale, Dec 2024
```

Querying the wrong one gives outdated answers — the stale DB listed 13 users including names that no longer exist (`emir`, `diego`, `Ruheri`, `alanczrz`, `ramarm0825@gmail.com`). Backing up the whole `config` directory makes the distinction moot, but it matters for any inspection.

## Blocker: SSO-only users

`config/plugins/SSO Authentication_3.5.2.4` comes from [`9p4/jellyfin-plugin-sso`](https://github.com/9p4/jellyfin-plugin-sso), was built for Jellyfin **10.9**, and the upstream repo was **archived on 2026-05-12**:

> "Project archived because I'm tired of working on this after all the years."

No v12 build will ever come from it. Auth provider split in the live DB:

```
Jellyfin.Server.Implementations.Users.DefaultAuthenticationProvider   5 users
Jellyfin.Plugin.SSO_Auth.Api.SSOController                           4 users
```

**Those 4 users have no local password.** Jellyfin 12 refuses to load plugins built for 10.11 (backend moved to .NET 10), so upgrading without a plan locks them out.

It is already partly broken on 10.11.11 — this repeats in the logs:

```
[WRN] UserManager: User "Terreneitor" was found with invalid/missing Authentication
Provider "Jellyfin.Plugin.SSO_Auth.Api.SSOController". Assigning user to
InvalidAuthProvider until this is corrected
```

### Stale OIDC config (independent of the upgrade)

`config/plugins/configurations/SSO-Auth.xml` points at **Authentik**:

```
https://auth.bowline.im/application/o/jellyfin/.well-known/openid-configuration
```

But `auth.bowline.im` is now served by **Pocket ID** (`ghcr.io/pocket-id/pocket-id:v2`). The OIDC config needs rewriting for Pocket ID whenever SSO is restored — worth fixing regardless of the version bump.

Note the XML also contains the plaintext `OidSecret` for the old Authentik client. It is dead config, but it is a live-looking credential sitting in the config directory (and therefore in every nightly backup archive).

### Replacement option

[`Flowfin/jellyfin-plugin-sso`](https://github.com/Flowfin/jellyfin-plugin-sso) is a maintained community fork. `5.0.0-JF12-beta.75` targets Jellyfin 12.0/.NET 10, but its own release notes state it has **"had no manual Release-QA pass against a live Jellyfin 12.0 server."** Beta, unproven — a reason to let it mature.

## Other v12 Preconditions (all checked)

- ✅ **Upgrade path** — 12.0 accepts direct upgrades from 10.10.7 or any 10.11.x. We are on 10.11.11.
- ✅ **Username case collisions** — usernames became case-insensitive; two accounts differing only by capitalization **fail the migration**. Verified none:
  `Terreneitor, admin, bowlinedandy, jp, lupita, mirivera, mons, pazthor, susifluna`
- ⚠️ **Third-party plugins** — release notes say remove them all before upgrading. Only the SSO plugin is installed on disk. Log namespaces also show `PlaybackReporting`, `Reports`, `YoutubeMetadata`, and `OpenSubtitles` are/were active; `configurations/` additionally holds an orphaned `LDAP-Auth.xml` for an already-absent plugin.

## Breaking Changes Relevant to This Setup

- **Irreversible migration.** _"database changes that prevent rolling back without a full restore."_ No downgrade without a pre-upgrade backup.
- **Full library scan REQUIRED after upgrading.** Auto-resolved alternate versions are dropped by the migration; only a scan restores them. First scan runs much longer than usual and some items may appear newly added.
- **Legacy `/emby/*` and `/mediabrowser/*` routes removed**; legacy authorization disabled by default. Very old third-party clients will break.
- **Plugin repo URL** must be reset to `https://repo.jellyfin.org/files/plugin/manifest.json`.
- Global subtitle settings moved to per-library; `.ogg` is now audio-only; symlinks resolved only at playback time; image upscaling removed; library sort order may shift.

## When We Pick This Up

1. **Fresh manual backup, container stopped first** — a 486 MB SQLite DB copied hot with a live WAL can restore inconsistent:
   ```bash
   cd ~/homelab/jellyfin && docker compose stop jellyfin
   sudo cp -a /mnt/docker-data/jellyfin/config \
              /mnt/docker-data/jellyfin/config.bak-10.11.11
   ```
   Don't lean on the nightly job alone: `offen/docker-volume-backup` covers `/mnt/docker-data`, but it runs at 04:00 local and is **local-only** — the Backblaze B2 job in `backup/docker-compose.yml` is entirely commented out.
2. **Resolve the 4 SSO users** — set local passwords while still on 10.11.11 and verify each can log in, and/or install the Flowfin JF12 build once it has real-world QA. Reconfigure OIDC for Pocket ID, not Authentik.
3. **Remove the incompatible plugin** — `rm -rf "config/plugins/SSO Authentication_3.5.2.4"`. Leave `configurations/*.xml` (inert, preserves settings for reinstall).
4. **Bump the tag** in `jellyfin/docker-compose.yml`, keeping an exact pin rather than `:latest`:
   ```diff
   -    image: lscr.io/linuxserver/jellyfin:10.11.11
   +    image: lscr.io/linuxserver/jellyfin:12.0ubu2604-ls48
   ```
   Nothing else in the service needs to change — the `jellyfin-amd` mod, `/dev/kfd`, `/dev/dri`, `group_add`, Traefik labels and the `8096` host port are all unaffected.
5. **Start and do not interrupt** the migration; watch `docker compose logs -f jellyfin`.
6. **Post-upgrade:** run the full library scan, reset the plugin repo URL, re-verify VAAPI on `/dev/dri/renderD128` in Dashboard → Playback, hard-refresh the web UI.

### Verification checklist

- Migrations completed with no unhandled exceptions and no `InvalidAuthProvider` warnings
- Login works for both a local-password user **and** a formerly-SSO user
- A forced transcode uses VAAPI, not software fallback
- Library and alternate versions intact after the full scan
- `https://flix.bowline.im` via Traefik **and** `http://<host>:8096` on the LAN
- **Jellyseerr** still reaches the Jellyfin API — it shares this compose file and is pinned to the floating pre-release tag `fallenbagel/jellyseerr:preview-OIDC`

### Rollback (only possible via step 1's copy)

```bash
cd ~/homelab/jellyfin && docker compose down
sudo rm -rf /mnt/docker-data/jellyfin/config
sudo mv /mnt/docker-data/jellyfin/config.bak-10.11.11 /mnt/docker-data/jellyfin/config
git checkout jellyfin/docker-compose.yml && docker compose up -d
```

Keep the backup until v12 has been stable for several days.

## Incidental Findings

- **`CLAUDE.md` lists Watchtower under "Core Infrastructure", but no Watchtower service exists anywhere in the repo** and there are no `com.centurylinklabs.watchtower.*` labels. Nothing auto-updates. Stale documentation worth correcting — it also means the 10.11.11 pin was never at risk of drifting on its own.
- **`jellyfin/.env.example` is missing `MEDIA_SHARE`**, which `docker-compose.yml` requires for both services. A fresh clone would silently bind-mount the wrong paths.
- The nightly backup includes `config/cache` (transcode scratch, ~635 MB) — wasted archive space.
- Jellyfin and Jellyseerr publish host ports in addition to Traefik routing, bypassing the `global-chain` security-headers/rate-limit middleware for anything that can reach the host directly.

## References

- [Jellyfin 12.0 release notes](https://github.com/jellyfin/jellyfin/releases/tag/v12.0)
- [Jellyfin 12.0 announcement post](https://jellyfin.org/posts/jellyfin-release-12.0/)
- [LinuxServer jellyfin tags](https://hub.docker.com/r/linuxserver/jellyfin/tags)
- [`9p4/jellyfin-plugin-sso`](https://github.com/9p4/jellyfin-plugin-sso) (archived)
- [`Flowfin/jellyfin-plugin-sso`](https://github.com/Flowfin/jellyfin-plugin-sso) (community fork, JF12 beta)
