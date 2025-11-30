#!/bin/bash
# Script to add docker-volume-backup.stop-during-backup=true label to all services

HOMELAB_DIR="/home/bowlinedandy/homelab"
LABEL='      - "docker-volume-backup.stop-during-backup=true"'

# List of directories to process (excluding backup itself)
DIRS=(
  "docmost" "pingvin-share" "open-webui" "hoarder" "ollama" "searxng"
  "metube" "traefik" "comfy-ui" "adguard" "orbi" "grafana"
  "icloud-photos-downloader" "pinchflat" "tailscale" "jarvis" "forgejo"
  "matrix" "home-assistant" "bluebubbles" "calibre" "grow-buddy"
)

for dir in "${DIRS[@]}"; do
  COMPOSE_FILE="$HOMELAB_DIR/$dir/docker-compose.yml"

  if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Skipping $dir - no docker-compose.yml found"
    continue
  fi

  # Check if label already exists
  if grep -q "docker-volume-backup.stop-during-backup" "$COMPOSE_FILE"; then
    echo "✓ $dir - label already exists"
    continue
  fi

  # Check if file has labels section
  if ! grep -q "labels:" "$COMPOSE_FILE"; then
    echo "⚠ $dir - no labels section found, needs manual addition"
    continue
  fi

  echo "Adding label to $dir..."

  # Create backup
  cp "$COMPOSE_FILE" "$COMPOSE_FILE.bak"

  # Add label to the first labels: section found
  # This adds it as the last label in the section
  awk '
    /labels:/ {
      in_labels = 1
      print
      next
    }
    in_labels && /^[^ ]/ {
      # End of labels section (new top-level key)
      print "      - \"docker-volume-backup.stop-during-backup=true\""
      in_labels = 0
    }
    in_labels && /^  [a-z]/ {
      # End of labels section (new service-level key)
      print "      - \"docker-volume-backup.stop-during-backup=true\""
      in_labels = 0
    }
    { print }
  ' "$COMPOSE_FILE.bak" > "$COMPOSE_FILE"

  echo "✓ $dir - label added"
done

echo ""
echo "Done! Backups created with .bak extension"
echo "Review the changes and remove .bak files when satisfied"
