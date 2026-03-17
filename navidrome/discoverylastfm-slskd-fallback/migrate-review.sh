#!/usr/bin/env bash
# Migration review script: list slskd downloads that match processed.json entries
# and output proposed mv commands for manual review.
#
# Usage: bash migrate-review.sh [processed.json] [slskd_downloads_dir] [music_inbox_dir]
#
# Delete this script after migration is complete.

set -euo pipefail

PROCESSED_JSON="${1:-/mnt/docker-data/discoverylastfm-slskd-fallback/processed.json}"
SLSKD_DL_DIR="${2:-/mnt/media/downloads/slskd/downloads}"
MUSIC_INBOX="${3:-/mnt/media/media/music-inbox}"

if [[ ! -f "$PROCESSED_JSON" ]]; then
    echo "Error: processed.json not found at $PROCESSED_JSON"
    exit 1
fi

if [[ ! -d "$SLSKD_DL_DIR" ]]; then
    echo "Error: slskd downloads dir not found at $SLSKD_DL_DIR"
    exit 1
fi

echo "# Migration review: slskd downloads -> music-inbox"
echo "# Source: $SLSKD_DL_DIR"
echo "# Destination: $MUSIC_INBOX"
echo "# Processed entries from: $PROCESSED_JSON"
echo "#"
echo "# Review the commands below, uncomment the ones you want to run,"
echo "# then execute this script output through bash."
echo ""

# Iterate over each user directory in slskd downloads
for user_dir in "$SLSKD_DL_DIR"/*/; do
    [[ -d "$user_dir" ]] || continue
    # Check album subdirectories
    find "$user_dir" -mindepth 1 -maxdepth 2 -type d | while read -r album_dir; do
        # Only consider dirs that contain audio files
        audio_count=$(find "$album_dir" -maxdepth 1 -type f \( -iname '*.flac' -o -iname '*.mp3' \) 2>/dev/null | wc -l)
        if [[ "$audio_count" -gt 0 ]]; then
            dirname=$(basename "$album_dir")
            echo "# Found: $album_dir ($audio_count audio files)"
            echo "# mv \"$album_dir\" \"$MUSIC_INBOX/$dirname\""
            echo ""
        fi
    done
done

echo "# Done. Review above commands, uncomment desired ones, and run."
