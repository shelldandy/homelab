#!/usr/bin/env bash
# Interactive migration script: move slskd downloads to music-inbox.
# Uses fzf for multi-select. Tab to select, Enter to confirm.
#
# Usage: bash migrate-review.sh [slskd_downloads_dir] [music_inbox_dir]
#
# Delete this script after migration is complete.

set -euo pipefail

SLSKD_DL_DIR="${1:-/mnt/navidrome/share/downloads/slskd/downloads}"
MUSIC_INBOX="${2:-/mnt/navidrome/share/media/music-inbox}"

if ! command -v fzf &>/dev/null; then
    echo "Error: fzf is not installed"
    exit 1
fi

if [[ ! -d "$SLSKD_DL_DIR" ]]; then
    echo "Error: slskd downloads dir not found at $SLSKD_DL_DIR"
    exit 1
fi

mkdir -p "$MUSIC_INBOX"

# Build list of album dirs with audio file counts
entries=()
while IFS= read -r album_dir; do
    audio_count=$(find "$album_dir" -maxdepth 1 -type f \( -iname '*.flac' -o -iname '*.mp3' \) 2>/dev/null | wc -l)
    if [[ "$audio_count" -gt 0 ]]; then
        parent=$(basename "$(dirname "$album_dir")")
        dirname=$(basename "$album_dir")
        entries+=("$(printf '%s/%s\t(%d files)\t%s' "$parent" "$dirname" "$audio_count" "$album_dir")")
    fi
done < <(find "$SLSKD_DL_DIR" -mindepth 2 -maxdepth 3 -type d)

if [[ ${#entries[@]} -eq 0 ]]; then
    echo "No album directories with audio files found in $SLSKD_DL_DIR"
    exit 0
fi

selected=$(printf '%s\n' "${entries[@]}" | fzf --multi --delimiter='\t' --with-nth=1,2 \
    --header="Tab=select  Enter=move  Esc=cancel" \
    --prompt="Select albums to move> " \
    --bind="ctrl-a:select-all" \
    || true)

if [[ -z "$selected" ]]; then
    echo "Nothing selected."
    exit 0
fi

moved=0
skipped=0

while IFS= read -r line; do
    album_dir=$(echo "$line" | awk -F'\t' '{print $NF}')
    dirname=$(basename "$album_dir")
    dest="$MUSIC_INBOX/$dirname"

    if [[ -d "$dest" ]]; then
        echo "  skip (exists): $dirname"
        ((skipped++))
    else
        mv "$album_dir" "$dest"
        echo "  moved: $dirname"
        ((moved++))
    fi
done <<< "$selected"

echo ""
echo "Done. Moved $moved, skipped $skipped."
