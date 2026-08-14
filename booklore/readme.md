# BookLore

BookLore is an ebook library management server with native Kobo sync support.

## Services

- **booklore**: Main ebook server at `books.bowline.im`
- **booklore-db**: MariaDB database for BookLore
- **bookdl**: Book downloader at `bookdl.bowline.im` (outputs to BookLore's bookdrop folder)
- **cloudflarebypassforscraping**: Cloudflare bypass proxy for bookdl
- **crossbill**: KOReader reading companion at `crossbill.bowline.im`
- **crossbill-db**: Postgres (pgvector) database for Crossbill

## Setup

1. Create the required directories:
   ```bash
   mkdir -p /mnt/docker-data/calibre/booklore/{data,mariadb}
   mkdir -p /mnt/docker-data/calibre/crossbill/{postgres,book-files}
   mkdir -p /mnt/media-merged/share/media/books/{booklore-library,booklore-bookdrop}
   ```

2. Copy `.env.example` to `.env` and fill in the values

3. Start the services:
   ```bash
   docker compose up -d
   ```

4. Access BookLore at `https://books.bowline.im`

5. Create a library pointing to `/books` and configure BookDrop to `/bookdrop`

## Kobo Sync

BookLore has native Kobo sync support. Configure your Kobo device to sync with the server via Device Settings in BookLore.

## bookdl

The book downloader service allows searching and downloading ebooks. Downloaded books are placed in the bookdrop folder and automatically imported by BookLore.

Access at `https://bookdl.bowline.im` (protected by OIDC auth).

## Crossbill

Reading companion that ingests highlights from KOReader and turns them into
chapter summaries, notes and flashcards. Upstream:
https://github.com/Crossbill-App/crossbill-web

It shares nothing with BookLore or bookdl - no common API, library or import
path. It lives in this stack only for convenience; its sole data source is the
KOReader plugin, so it is useful only if you read on a KOReader device.

Install [koreader-plugin](https://github.com/Crossbill-App/koreader-plugin)
into `koreader/plugins/` on the device and point it at
`https://crossbill.bowline.im`. The plugin stores your **actual account
username and password** on the device and replays them on every re-login -
there is no API token or app password mechanism.

Before first start, generate the three mandatory secrets into `.env`; the
backend refuses to boot without them:

```bash
openssl rand -hex 32     # CROSSBILL_SECRET_KEY
openssl rand -hex 32     # CROSSBILL_REFRESH_TOKEN_SECRET_KEY (must differ)
openssl rand -base64 24  # CROSSBILL_ADMIN_PASSWORD
```

### No Pocket ID SSO

Unlike bookdl, Crossbill is not behind `oidc-auth` and has no native OIDC
support either. Its own username/password login is the security boundary -
hence the strong admin password and `ALLOW_USER_REGISTRATIONS=false`.

Forward auth cannot be used here: the KOReader plugin is a LuaSocket HTTP
client with no cookie jar that checks `code == 200` on every request, so the
middleware's 302 redirect to Pocket ID breaks sync at the login step. It would
also chase that cross-host redirect and send the username and password toward
the identity provider. Excluding `PathPrefix('/api')` would restore sync, but
`/api/v1` is Crossbill's entire application surface - the page at `/` is just a
static bundle calling those same endpoints - so the gate would protect nothing
of substance while looking like it did.

### Notes

- Image is on Docker Hub (`tumetsu/crossbill`), not ghcr.io, and is **amd64
  only**.
- No `PUID`/`PGID` support: the container runs as root, so files under
  `crossbill/book-files/` and `crossbill/postgres/` are root-owned. The
  `PUID`/`PGID` at the top of `.env` do not apply to it.
- `TRUSTED_PROXY_HOPS=1` because Traefik appends to `X-Forwarded-For`. Left at
  the default `0`, per-IP rate limiting would key on Traefik's address and put
  every client in one bucket. Set `CROSSBILL_LOG_PROXY_CHAIN=true` briefly to
  verify, then turn it off.
- The background worker runs in-process (`EMBEDDED_WORKER` defaults to true),
  so upstream's separate `worker` and `garage` (S3) services are not deployed.
- AI chapter digests and semantic search are optional and off; see the
  `AI_PROVIDER` and `EMBEDDING_PROVIDER` blocks in upstream's
  [.env.example](https://github.com/Crossbill-App/crossbill-web/blob/main/.env.example).
