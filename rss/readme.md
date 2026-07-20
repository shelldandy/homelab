# RSS (Miniflux + ReactFlux)

Miniflux is the RSS backend/API server. ReactFlux is a nicer web client for it.

## Services

- **miniflux**: RSS backend + API + built-in web UI at `miniflux.bowline.im`
- **miniflux-db**: Postgres database for Miniflux
- **reactflux**: Alternative web UI for Miniflux at `rss.bowline.im`

## Setup

1. Copy `.env.example` to `.env` and fill in the values.

2. Create a Pocket ID OIDC client for Miniflux:
   - Redirect URL: `https://miniflux.bowline.im/oauth2/oidc/callback`
   - Put the resulting client ID/secret into `MINIFLUX_OIDC_CLIENT_ID` / `MINIFLUX_OIDC_CLIENT_SECRET` in `.env`

3. Start the services:
   ```bash
   docker compose up -d
   ```

4. Visit `https://miniflux.bowline.im` and log in via Pocket ID. The first OIDC login creates your Miniflux account.

5. Visit `https://rss.bowline.im` (ReactFlux) and log in with your Miniflux username/password, or generate an API key from Miniflux's settings and use that instead.
