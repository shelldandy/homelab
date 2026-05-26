#!/bin/bash

# Detect fake/malware torrents by checking for dangerous file extensions
# and the absence of valid media files.
#
# Usage: detect-fake.sh "<content_path>"
# qBittorrent "Run after download" command: /scripts/detect-fake.sh "%F"

CONTENT_PATH="$1"
DANGEROUS_EXTS="lnk|scr|iso|arj|exe|bat|cmd|com|msi|vbs"
MEDIA_EXTS="mkv|mp4|avi|m4v|ts|flv|webm|wmv|mov|flac|mp3|opus|ogg|m4a|wav|aac"

if [ -z "$CONTENT_PATH" ]; then
    echo "[detect-fake] No path provided"
    exit 1
fi

if [ ! -e "$CONTENT_PATH" ]; then
    echo "[detect-fake] Path does not exist: $CONTENT_PATH"
    exit 1
fi

if [ -f "$CONTENT_PATH" ]; then
    search_dir="$(dirname "$CONTENT_PATH")"
    search_target="$CONTENT_PATH"
else
    search_dir="$CONTENT_PATH"
    search_target="$CONTENT_PATH"
fi

media_count=$(find "$search_target" -type f -regextype posix-extended \
    -iregex ".*\.(${MEDIA_EXTS})" 2>/dev/null | wc -l)

dangerous_files=$(find "$search_target" -type f -regextype posix-extended \
    -iregex ".*\.(${DANGEROUS_EXTS})" 2>/dev/null)
dangerous_count=$(echo "$dangerous_files" | grep -c . 2>/dev/null)

if [ "$media_count" -eq 0 ] && [ "$dangerous_count" -gt 0 ]; then
    echo "[detect-fake] FAKE TORRENT DETECTED: $CONTENT_PATH"
    echo "[detect-fake] No media files found, but $dangerous_count dangerous file(s):"
    echo "$dangerous_files"
    exit 1
fi

if [ "$dangerous_count" -gt 0 ]; then
    echo "[detect-fake] WARNING: $CONTENT_PATH contains $dangerous_count dangerous file(s) alongside $media_count media file(s):"
    echo "$dangerous_files"
fi

exit 0
