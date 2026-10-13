# RSS (Miniflux + ReactFlux)

Miniflux is the RSS backend/API server. ReactFlux is a nicer web client for it.

## Services

- **miniflux**: RSS backend + API + built-in web UI at `miniflux.bowline.im`
- **miniflux-db**: Postgres database for Miniflux
- **reactflux**: Alternative web UI for Miniflux at `rss.bowline.im`
- **miniflux-ai**: Adds an AI summary to new entries using the shared [Ollama](../ollama) (`qwen3:4b-instruct`). No UI; configured via `config.yml`

## Setup

1. Copy `.env.example` to `.env` and fill in the values.

2. Create a Pocket ID OIDC client for Miniflux:
   - Redirect URL: `https://miniflux.bowline.im/oauth2/oidc/callback`
   - Put the resulting client ID/secret into `MINIFLUX_OIDC_CLIENT_ID` / `MINIFLUX_OIDC_CLIENT_SECRET` in `.env`

3. Set up miniflux-ai (needs the `ollama` stack running and the model pulled: `docker exec ollama ollama pull qwen3:4b-instruct`):
   - Log in to Miniflux once (step 5 below), then create an API key under Settings > API Keys.
   - `cp config.yml.example config.yml` and put the key in `miniflux.api_key`.
   - Until `config.yml` exists, the miniflux-ai container will fail to start; that's expected.

4. Start the services:
   ```bash
   docker compose up -d
   ```

5. Visit `https://miniflux.bowline.im` and log in via Pocket ID. The first OIDC login creates your Miniflux account.

6. Visit `https://rss.bowline.im` (ReactFlux) and log in with your Miniflux username/password, or generate an API key from Miniflux's settings and use that instead.
