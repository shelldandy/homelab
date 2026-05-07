#!/usr/bin/env bash
# Interactive migration script: move slskd downloads to music-inbox.
# Filters out albums that already exist in the navidrome library.
# Uses fzf for multi-select. Tab to select, Enter to confirm.
#
# Usage: bash migrate-review.sh [slskd_downloads_dir] [music_inbox_dir] [music_library_dir]
#
# Delete this script after migration is complete.

set -euo pipefail

SLSKD_DL_DIR="${1:-/mnt/navidrome/share/downloads/slskd/downloads}"
MUSIC_INBOX="${2:-/mnt/navidrome/share/media/music-inbox}"
MUSIC_LIB="${3:-/mnt/navidrome/share/media/music}"

if ! command -v fzf &>/dev/null; then
    echo "Error: fzf is not installed"
    exit 1
fi

if [[ ! -d "$SLSKD_DL_DIR" ]]; then
    echo "Error: slskd downloads dir not found at $SLSKD_DL_DIR"
    exit 1
fi

mkdir -p "$MUSIC_INBOX"

# Normalize a string for comparison: lowercase, strip punctuation/whitespace
normalize() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g'
}

# Check if an artist/album already exists in the navidrome library
album_exists_in_library() {
    local artist="$1"
    local album="$2"
    local norm_album
    norm_album=$(normalize "$album")

    # Find artist dir (case-insensitive)
    local artist_dir
    artist_dir=$(find "$MUSIC_LIB" -maxdepth 1 -type d -iname "$artist" 2>/dev/null | head -1)
    [[ -z "$artist_dir" ]] && return 1

    # Check album subdirs
    while IFS= read -r subdir; do
        local subdir_name
        subdir_name=$(basename "$subdir")
        # Strip year suffix like "(2024)" for comparison
        subdir_name=$(echo "$subdir_name" | sed 's/ *([0-9]\{4\})$//')
        if [[ "$(normalize "$subdir_name")" == "$norm_album" ]]; then
            return 0
        fi
    done < <(find "$artist_dir" -maxdepth 1 -type d -mindepth 1 2>/dev/null)

    return 1
}

# Build list of album dirs, filtering out ones already in library
entries=()
skipped_existing=0
while IFS= read -r album_dir; do
    audio_count=$(find "$album_dir" -maxdepth 1 -type f \( -iname '*.flac' -o -iname '*.mp3' \) 2>/dev/null | wc -l)
    if [[ "$audio_count" -gt 0 ]]; then
        dirname=$(basename "$album_dir")
        # Parse "Artist - Album (Year)_N" format
        # Strip trailing _N duplicate suffix
        clean_name=$(echo "$dirname" | sed 's/_[0-9]*$//')
        if [[ "$clean_name" =~ ^(.*[^ ])\ -\ (.*)$ ]]; then
            artist="${BASH_REMATCH[1]}"
            # Strip [brackets] from artist name (e.g. [ocean jams])
            artist=$(echo "$artist" | sed 's/^\[//;s/\]$//')
            # Strip year from album: "Album (2024)" -> "Album"
            album=$(echo "${BASH_REMATCH[2]}" | sed 's/ *([0-9]\{4\})$//')

            if album_exists_in_library "$artist" "$album"; then
                skipped_existing=$((skipped_existing + 1))
                continue
            fi
        fi

        parent=$(basename "$(dirname "$album_dir")")
        entries+=("$(printf '%s/%s\t(%d files)\t%s' "$parent" "$dirname" "$audio_count" "$album_dir")")
    fi
done < <(find "$SLSKD_DL_DIR" -mindepth 2 -maxdepth 3 -type d)

echo "Filtered out $skipped_existing album(s) already in library"

if [[ ${#entries[@]} -eq 0 ]]; then
    echo "No new album directories to migrate."
    exit 0
fi

echo "${#entries[@]} album(s) remaining"
echo ""

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
        skipped=$((skipped + 1))
    else
        mv "$album_dir" "$dest"
        echo "  moved: $dirname"
        moved=$((moved + 1))
    fi
done <<< "$selected"

echo ""
echo "Done. Moved $moved, skipped $skipped."
