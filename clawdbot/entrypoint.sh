#!/bin/sh
# Read OAuth token from Claude credentials file and export it
if [ -f "/home/node/.claude/.credentials.json" ]; then
  export ANTHROPIC_OAUTH_TOKEN=$(node -e "console.log(JSON.parse(require('fs').readFileSync('/home/node/.claude/.credentials.json')).claudeAiOauth?.accessToken || '')")
fi

exec "$@"
