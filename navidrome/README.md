# [Navidrome](https://www.navidrome.org/)

Navidrome is a self-hosted, open source music server and streamer. It gives you freedom to listen to your music collection from any browser or mobile device.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             Music Discovery                              │
├───────────────────────┬──────────────────────────────────────────────────┤
│   discoverylastfm     │            lastfm-album-selector                 │
│ (add new artists from │  (monitor top Last.fm albums for existing Lidarr │
│  Last.fm listening)   │   artists; MusicBrainz-pinned disambiguation)    │
└──────────┬────────────┴────────────────────┬─────────────────────────────┘
           │                                 │
           ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Music Sources                            │
├─────────────────────────────┬───────────────────────────────────┤
│         Lidarr              │           Manual/Slskd            │
│    (automated downloads)    │        (manual downloads)         │
└──────────────┬──────────────┴─────────────────┬─────────────────┘
               │                                │
               ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│   /share/media/music     │    │   /share/media/music-inbox       │
│   (final library)        │    │   (beets inbox)                  │
└──────────────────────────┘    └─────────────────┬────────────────┘
               │                                  │
               │                                  ▼
               │                    ┌──────────────────────────────┐
               │                    │   Beets (auto-tag & move)    │
               │                    └─────────────────┬────────────┘
               │                                      │
               ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    /share/media/music                           │
│                    (Navidrome library)                          │
└─────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Navidrome                               │
│                    (music streaming)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Description | Port |
|---------|-------------|------|
| Navidrome | Music streaming server | 4533 |
| Lidarr | Music collection manager | 8686 |
| Soularr | Lidarr → Slskd bridge | - |
| Beets | Music tagger and organizer | 5001 |
| Slskd | Soulseek client | 5030 |
| discoverylastfm | Add new artists from Last.fm listening history | - |
| lastfm-album-selector | Monitor top Last.fm albums for existing Lidarr artists | - |

## Music Workflows

### Lidarr (Automated)
Lidarr downloads music directly to `/share/media/music`. Files are already tagged with MusicBrainz metadata and ready for Navidrome.

### Beets Inbox (Manual)
Music added to `/share/media/music-inbox` (e.g., via Slskd or manual copy) is automatically processed by Beets:
- Auto-tagged using MusicBrainz
- Moved to `/share/media/music`
- Album art fetched and embedded

Beets-flask GUI available for manual review if needed.

## Soularr

Soularr bridges Lidarr and Slskd, searching Soulseek for music missing in Lidarr and triggering downloads.

## Last.fm Integration

Two services handle Last.fm-driven music discovery:

### discoverylastfm
Runs weekly (cron). Scans your Last.fm listening history and adds artists with recent plays to Lidarr.

### lastfm-album-selector
Runs hourly. For each artist already in Lidarr with no monitored albums, queries Last.fm for their top albums and monitors the top N in Lidarr, then triggers a search. Uses MusicBrainz IDs to pin the Last.fm lookup to the exact artist (avoids wrong-artist disambiguation like "Ye" → Yes). After 3 failed matches, falls back to the most recently released album in Lidarr.

Configure via environment variables:
- `TOP_ALBUMS_COUNT` — number of albums to monitor per artist (default: 2)
- `MAX_RETRIES` — failed match attempts before fallback (default: 3)
- `LOG_LEVEL` — set to `DEBUG` to log Last.fm/Lidarr title comparisons
