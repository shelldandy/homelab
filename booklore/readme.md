# BookLore

BookLore is an ebook library management server with native Kobo sync support.

## Services

- **booklore**: Main ebook server at `books.bowline.im`
- **booklore-db**: MariaDB database for BookLore
- **bookdl**: Book downloader at `bookdl.bowline.im` (outputs to BookLore's bookdrop folder)
- **cloudflarebypassforscraping**: Cloudflare bypass proxy for bookdl

## Setup

1. Create the required directories:
   ```bash
   mkdir -p /mnt/docker-data/calibre/booklore/{data,mariadb}
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
