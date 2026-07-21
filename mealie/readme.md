# Mealie

Self-hosted recipe manager and meal planner, backed by Postgres with Pocket ID SSO.

## Services

- **mealie**: Recipe manager web UI + API at `mealie.bowline.im`
- **mealie-db**: Postgres database for Mealie

## Setup

1. Copy `.env.example` to `.env` and fill in the values.

2. Create a Pocket ID OIDC client for Mealie
   (see [Pocket ID's Mealie example](https://pocket-id.org/docs/client-examples/mealie)):
   - Callback URL: `https://mealie.bowline.im/login` (matched exactly — no trailing slash)
   - Put the resulting client ID/secret into `MEALIE_OIDC_CLIENT_ID` /
     `MEALIE_OIDC_CLIENT_SECRET` in `.env`
   - Members of the Pocket ID group named by `MEALIE_OIDC_ADMIN_GROUP` become
     Mealie admins automatically.

3. Fill in the `SMTP_*` values in `.env` to enable invites and password resets.

4. Start the services:

   ```bash
   docker compose up -d
   ```

5. Visit `https://mealie.bowline.im`. `OIDC_AUTO_REDIRECT` is on, so you go straight
   to Pocket ID; the first login creates your Mealie account.

## Notes

- Because `OIDC_AUTO_REDIRECT=true`, the local login form is bypassed. To reach it
  (e.g. if SSO breaks), use `https://mealie.bowline.im/login?direct=1` —
  `ALLOW_PASSWORD_LOGIN` is left enabled as a fallback.
- Admin rights come from the `OIDC_ADMIN_GROUP` claim. Login is not otherwise
  restricted — add `OIDC_USER_GROUP` if you want to limit who can sign in at all.
- Persistent data lives under `${CONFIG_PATH}` — `data/` for Mealie's app data
  (recipes, images) and `postgres/` for the database.
