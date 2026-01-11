# ClawdBot

Telegram AI assistant powered by Claude, using [ClawdBot](https://docs.clawd.bot/) gateway.

## Setup

1. **Create Telegram bot** via [@BotFather](https://t.me/BotFather):
   - Send `/newbot`, choose name and username (must end in `bot`)
   - Copy the token to `.env`

2. **Copy `.env.example` to `.env`** and fill in values:
   ```bash
   cp .env.example .env
   ```

3. **Set up Claude Code OAuth token**:
   - Run `claude` CLI and authenticate
   - Copy access token from `~/.claude/.credentials.json` to `ANTHROPIC_OAUTH_TOKEN` in `.env`

4. **Create config directories**:
   ```bash
   mkdir -p config/.claude config/.pi/agent workspace
   ```

5. **Start the service**:
   ```bash
   docker compose up -d
   ```

6. **Approve Telegram pairing** - First message to bot returns a pairing code:
   ```bash
   docker exec clawdbot node dist/index.js pairing approve telegram <CODE>
   ```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `CLAWDBOT_GATEWAY_TOKEN` | Gateway auth token (generate with `openssl rand -hex 32`) |
| `ANTHROPIC_OAUTH_TOKEN` | Claude OAuth access token from `~/.claude/.credentials.json` |

### Key Files

- `config/clawdbot.json` - Main ClawdBot configuration
- `config/agents/main/agent/auth-profiles.json` - OAuth credentials store
- `config/.claude/.credentials.json` - Claude Code credentials (for auto-sync)
- `config/.pi/agent/auth.json` - Legacy pi-agent auth (optional)

## Important Notes

### OAuth Token Setup

The embedded pi-ai library reads `ANTHROPIC_OAUTH_TOKEN` environment variable, **not** auth files. This is the key to making Claude Code OAuth work:

```yaml
environment:
  - ANTHROPIC_OAUTH_TOKEN=${ANTHROPIC_OAUTH_TOKEN}
```

The `auth-profiles.json` and file-based auth are used by ClawdBot's gateway layer but the underlying pi-ai library for actual API calls requires the env var.

### Token Refresh

OAuth tokens expire (typically ~7 hours). When the token expires:
1. Re-run `claude` CLI to refresh credentials
2. Copy new `accessToken` from `~/.claude/.credentials.json` to `.env`
3. Restart the container

### Model Configuration

Set in `config/clawdbot.json`:
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-20250514"
      }
    }
  }
}
```

Available models use `anthropic/` prefix (not `claudeAiOauth/`).

### Volume Mounts

| Mount | Purpose |
|-------|---------|
| `./config:/home/node/.clawdbot` | ClawdBot config and state |
| `./config/.claude:/home/node/.claude:ro` | Claude Code credentials (for sync) |
| `./config/.pi:/home/node/.pi:ro` | Legacy pi-agent auth |
| `./workspace:/home/node/clawd` | Agent workspace |

## Commands

```bash
# View logs
docker compose logs -f

# Run diagnostics
docker exec clawdbot node dist/index.js doctor

# Check model status
docker exec clawdbot node dist/index.js models status

# List available models
docker exec clawdbot node dist/index.js models list --all

# Approve Telegram pairing
docker exec clawdbot node dist/index.js pairing approve telegram <CODE>
```

## Troubleshooting

### "No API key found for anthropic"

The pi-ai library needs `ANTHROPIC_OAUTH_TOKEN` env var set. File-based auth alone is not sufficient.

### "Unknown model: claudeaioauth/..."

Use `anthropic/` prefix for models, not `claudeAiOauth/`.

### Token expiration

Run `docker exec clawdbot node dist/index.js doctor` - it will show auth status and expiration times.
