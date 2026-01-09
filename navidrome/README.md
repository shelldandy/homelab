# [Navidrome](https://www.navidrome.org/)

Navidrome is a self-hosted, open source music server and streamer. It gives you freedom to listen to your music collection from any browser or mobile device.

## Architecture

```
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
| Beets | Music tagger and organizer | 5001 |
| Slskd | Soulseek client | 5030 |

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
