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

3. **Ensure Claude Code is authenticated** on the host:

   ```bash
   claude  # This will prompt for auth if needed
   ```

   The container mounts `~/.claude` from the host and auto-reads the OAuth token on startup.

4. **Create config directories**:

   ```bash
   mkdir -p config workspace
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

| Variable                 | Description                                               |
| ------------------------ | --------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN`     | Bot token from @BotFather                                 |
| `CLAWDBOT_GATEWAY_TOKEN` | Gateway auth token (generate with `openssl rand -hex 32`) |

### Key Files

- `config/clawdbot.json` - Main ClawdBot configuration
- `config/agents/main/agent/auth-profiles.json` - OAuth credentials store
- `entrypoint.sh` - Reads OAuth token from host credentials on startup

## Important Notes

### OAuth Token Auto-Sync

The host's `~/.claude` directory is mounted read-only into the container. On startup, `entrypoint.sh` reads the OAuth token from `~/.claude/.credentials.json` and exports it as `ANTHROPIC_OAUTH_TOKEN`.

This means:
- **No manual token copying** - tokens stay in sync with the host
- **Token refresh** - just restart the container after Claude Code refreshes credentials
- The underlying pi-ai library requires the `ANTHROPIC_OAUTH_TOKEN` env var (file-based auth alone doesn't work)

### Token Refresh

OAuth tokens expire (typically ~7 hours). When the token expires:

1. Run any `claude` command on the host (this refreshes the token)
2. Restart the container: `docker compose restart`

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

| Mount                               | Purpose                                 |
| ----------------------------------- | --------------------------------------- |
| `./entrypoint.sh:/entrypoint.sh:ro` | Startup script to read OAuth token      |
| `./config:/home/node/.clawdbot`     | ClawdBot config and state               |
| `~/.claude:/home/node/.claude:ro`   | Host Claude credentials (for token sync)|
| `./workspace:/home/node/clawd`      | Agent workspace                         |

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

The pi-ai library needs `ANTHROPIC_OAUTH_TOKEN` env var set. Ensure:
1. Host has valid credentials in `~/.claude/.credentials.json`
2. Container was restarted after token refresh

### "Unknown model: claudeaioauth/..."

Use `anthropic/` prefix for models, not `claudeAiOauth/`.

### Token expiration (401 error)

1. Run any `claude` command on the host to refresh the token
2. Restart: `docker compose restart`
3. Verify with: `docker exec clawdbot node dist/index.js doctor`
