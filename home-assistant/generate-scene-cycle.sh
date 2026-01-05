#!/bin/bash
set -euo pipefail

# Scene Cycle Generator for Home Assistant
# Creates input_select, script, and automation for cycling through scene presets

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/configuration.yaml"
SCRIPTS_FILE="$SCRIPT_DIR/includes/scripts.yaml"
AUTOMATIONS_FILE="$SCRIPT_DIR/includes/automations.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Scene Cycle Generator for Home Assistant${NC}"
echo "=========================================="
echo ""

# Check dependencies
if ! command -v fzf &> /dev/null; then
    echo -e "${RED}Error: fzf is required but not installed.${NC}"
    echo "Install with: sudo apt install fzf"
    exit 1
fi

# Fetch available presets from the container
echo "Fetching available presets from Home Assistant..."
PRESETS=$(cd "$SCRIPT_DIR" && docker compose exec -T homeassistant cat /config/custom_components/scene_presets/presets.json 2>/dev/null | \
    python3 -c "import sys, json; d=json.load(sys.stdin); [print(f'{p[\"name\"]}:{p[\"id\"]}') for p in d['presets']]") || {
    echo -e "${RED}Error: Could not fetch presets. Is Home Assistant running?${NC}"
    exit 1
}

if [ -z "$PRESETS" ]; then
    echo -e "${RED}Error: No presets found.${NC}"
    exit 1
fi

# Get light entity ID
echo ""
read -p "Enter light entity ID (e.g., light.focos_sala): " LIGHT_ENTITY
if [ -z "$LIGHT_ENTITY" ]; then
    echo -e "${RED}Error: Light entity ID is required.${NC}"
    exit 1
fi

# Validate format
if [[ ! "$LIGHT_ENTITY" =~ ^light\. ]]; then
    echo -e "${YELLOW}Warning: Entity doesn't start with 'light.' - adding prefix${NC}"
    LIGHT_ENTITY="light.$LIGHT_ENTITY"
fi

# Get display name
echo ""
read -p "Enter display name (e.g., Focos Sala): " DISPLAY_NAME
if [ -z "$DISPLAY_NAME" ]; then
    echo -e "${RED}Error: Display name is required.${NC}"
    exit 1
fi

# Generate snake_case ID from display name
SCENE_ID=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]_')_scene

# Select presets with fzf
echo ""
echo -e "${YELLOW}Select presets (Tab to select multiple, Enter to confirm):${NC}"
SELECTED_PRESETS=$(echo "$PRESETS" | cut -d: -f1 | fzf --multi --height=20 --border --header="Select scene presets")

if [ -z "$SELECTED_PRESETS" ]; then
    echo -e "${RED}Error: At least one preset must be selected.${NC}"
    exit 1
fi

# Build preset map and options list
PRESET_MAP=""
OPTIONS_LIST=""
FIRST_OPTION=""

while IFS= read -r preset_name; do
    # Get UUID for this preset
    UUID=$(echo "$PRESETS" | grep "^${preset_name}:" | cut -d: -f2)

    if [ -z "$FIRST_OPTION" ]; then
        FIRST_OPTION="$preset_name"
    fi

    OPTIONS_LIST="${OPTIONS_LIST}      - \"${preset_name}\"\n"
    PRESET_MAP="${PRESET_MAP}          \"${preset_name}\": \"${UUID}\"\n"
done <<< "$SELECTED_PRESETS"

# Remove trailing newlines
OPTIONS_LIST=$(echo -e "$OPTIONS_LIST" | sed '/^$/d')
PRESET_MAP=$(echo -e "$PRESET_MAP" | sed '/^$/d')

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "  Light Entity: $LIGHT_ENTITY"
echo "  Display Name: $DISPLAY_NAME"
echo "  Scene ID: $SCENE_ID"
echo "  Selected Presets: $(echo "$SELECTED_PRESETS" | tr '\n' ', ' | sed 's/,$//')"
echo ""

read -p "Proceed with generating configuration? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Backup files
echo ""
echo "Creating backups..."
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
cp "$SCRIPTS_FILE" "${SCRIPTS_FILE}.bak"
cp "$AUTOMATIONS_FILE" "${AUTOMATIONS_FILE}.bak"

# Append to configuration.yaml (before prometheus: line)
echo "Updating configuration.yaml..."

# Create the new input_select block
NEW_INPUT_SELECT="  ${SCENE_ID}:
    name: \"${DISPLAY_NAME} Scene\"
    options:
${OPTIONS_LIST}
    initial: \"${FIRST_OPTION}\"
    icon: mdi:lightbulb-group

"

# Use Python for safe YAML insertion
python3 << PYEOF
import re

with open("$CONFIG_FILE", "r") as f:
    content = f.read()

new_block = """$NEW_INPUT_SELECT"""

# Insert before prometheus: line
if "prometheus:" in content:
    content = content.replace("prometheus:", new_block + "prometheus:")
else:
    # Append after input_select section
    content = content + "\n" + new_block

with open("$CONFIG_FILE", "w") as f:
    f.write(content)
PYEOF

# Append to scripts.yaml
echo "Updating includes/scripts.yaml..."
cat >> "$SCRIPTS_FILE" << EOF

# Cycle through ${DISPLAY_NAME} scene presets
cycle_${SCENE_ID}:
  alias: "Cycle ${DISPLAY_NAME} Scene"
  sequence:
    - service: input_select.select_next
      target:
        entity_id: input_select.${SCENE_ID}
      data:
        cycle: true
EOF

# Append to automations.yaml
echo "Updating includes/automations.yaml..."
cat >> "$AUTOMATIONS_FILE" << EOF

# Scene Presets Automation for ${DISPLAY_NAME}
- alias: "Ciclar ${DISPLAY_NAME}"
  trigger:
    - platform: state
      entity_id: input_select.${SCENE_ID}
  action:
    - variables:
        preset_map:
${PRESET_MAP}
    - service: scene_presets.apply_preset
      data:
        preset_id: "{{ preset_map[states('input_select.${SCENE_ID}')] }}"
        targets:
          entity_id: ${LIGHT_ENTITY}
        brightness: 150
        transition: 1
  mode: single
EOF

echo ""
echo -e "${GREEN}Configuration files updated successfully!${NC}"

# Reload Home Assistant configs
echo ""
echo "Reloading Home Assistant configurations..."

cd "$SCRIPT_DIR"

# Reload input_select
docker compose exec -T homeassistant python3 << 'PYTHON_EOF'
import requests
import os

api_url = "http://localhost:8123/api"
headers = {"Content-Type": "application/json"}

# Try to reload without auth first (internal access)
services = [
    ("input_select", "reload"),
    ("script", "reload"),
    ("automation", "reload"),
]

for domain, service in services:
    try:
        resp = requests.post(f"{api_url}/services/{domain}/{service}", headers=headers, timeout=10)
        if resp.status_code in [200, 201]:
            print(f"✓ Reloaded {domain}")
        else:
            print(f"✗ Failed to reload {domain}: {resp.status_code}")
    except Exception as e:
        print(f"✗ Failed to reload {domain}: {e}")
PYTHON_EOF

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "You can now use:"
echo "  - script.cycle_${SCENE_ID} to cycle through presets"
echo "  - input_select.${SCENE_ID} to view/set current preset"
echo ""
echo "If reload failed, manually reload in HA: Developer Tools > YAML > Reload"
