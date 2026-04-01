#!/usr/bin/env python3
"""Telegram bot for downloading FLAC music via SpotiFLAC with Spotify search."""

import logging
import os
import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from SpotiFLAC import SpotiFLAC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/share/media/music-inbox")

ALLOWED_USERS = {int(uid) for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",") if uid.strip()}

SPOTIFY_URL_RE = re.compile(r"https?://open\.spotify\.com/(track|album|playlist)/\S+")
APPLE_MUSIC_URL_RE = re.compile(r"https?://music\.apple\.com/.+/(album|playlist)/[^\s]+")
APPLE_MUSIC_TRACK_RE = re.compile(r"\?i=(\d+)")

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
    )
)


SERVICES = os.environ.get("SERVICES", "tidal,qobuz,apple-music,amazon,deezer").split(",")


def apple_music_to_spotify(url: str) -> tuple[str | None, str]:
    """Convert an Apple Music URL to a Spotify URL via search. Returns (spotify_url, message)."""
    try:
        import requests as req

        # Use Song.link/Odesli API to resolve Apple Music → Spotify
        resp = req.get("https://api.song.link/v1-alpha.1/links", params={"url": url}, timeout=15)
        if resp.ok:
            data = resp.json()
            spotify_url = data.get("linksByPlatform", {}).get("spotify", {}).get("url")
            if spotify_url:
                return spotify_url, ""
        # Fallback: extract album/track name from the URL path and search Spotify
        log.warning("Song.link lookup failed, falling back to Spotify search")
    except Exception as e:
        log.warning("Song.link lookup failed: %s", e)

    # Fallback: parse the URL path for album name
    from urllib.parse import urlparse

    path = urlparse(url).path  # e.g. /us/album/never-gonna-give-you-up/1558533900
    parts = [p for p in path.split("/") if p]
    # Find the segment after "album" or "playlist"
    query = None
    for i, part in enumerate(parts):
        if part in ("album", "playlist") and i + 1 < len(parts):
            query = parts[i + 1].replace("-", " ")
            break
    if not query:
        return None, "Could not parse Apple Music URL."

    is_track = bool(APPLE_MUSIC_TRACK_RE.search(url))
    search_type = "track" if is_track else "album"
    results = sp.search(q=query, type=search_type, limit=1)
    items = results.get(f"{search_type}s", {}).get("items", [])
    if items:
        return items[0]["external_urls"]["spotify"], ""
    return None, f"Could not find matching {search_type} on Spotify."


def download(url: str) -> str:
    """Download FLAC from a Spotify URL. Returns status message."""
    try:
        log.info("Downloading: %s", url)
        SpotiFLAC(url=url, output_dir=OUTPUT_DIR, services=SERVICES)
        return f"Downloaded to music-inbox."
    except Exception as e:
        log.error("Download failed for %s: %s", url, e)
        return f"Download failed: {e}"


def is_allowed(update: Update) -> bool:
    if not ALLOWED_USERS:
        return True
    return update.effective_user and update.effective_user.id in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "Send me a Spotify or Apple Music URL to download as FLAC, or search by typing a song/album name."
    )


async def resolve_and_download(url: str, msg) -> None:
    """Resolve Apple Music URLs if needed, then download."""
    if APPLE_MUSIC_URL_RE.match(url):
        await msg.edit_text("Resolving Apple Music URL...")
        spotify_url, err = apple_music_to_spotify(url)
        if not spotify_url:
            await msg.edit_text(err or "Could not resolve Apple Music URL.")
            return
        log.info("Resolved Apple Music → %s", spotify_url)
        url = spotify_url
    await msg.edit_text("Downloading...")
    result = download(url)
    await msg.edit_text(result)


async def cmd_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /dl <url>")
        return
    url = context.args[0]
    if not SPOTIFY_URL_RE.match(url) and not APPLE_MUSIC_URL_RE.match(url):
        await update.message.reply_text("Send a Spotify or Apple Music URL.")
        return
    msg = await update.message.reply_text("Processing...")
    await resolve_and_download(url, msg)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    text = update.message.text.strip()

    if SPOTIFY_URL_RE.match(text) or APPLE_MUSIC_URL_RE.match(text):
        msg = await update.message.reply_text("Processing...")
        await resolve_and_download(text, msg)
        return

    # Search Spotify
    msg = await update.message.reply_text(f"Searching for \"{text}\"...")
    try:
        results = sp.search(q=text, type="track", limit=5)
        tracks = results.get("tracks", {}).get("items", [])
    except Exception as e:
        log.error("Search failed: %s", e)
        await msg.edit_text(f"Search failed: {e}")
        return

    if not tracks:
        await msg.edit_text("No results found.")
        return

    buttons = []
    lines = []
    for i, t in enumerate(tracks):
        artists = ", ".join(a["name"] for a in t["artists"])
        label = f"{artists} — {t['name']}"
        lines.append(f"{i + 1}. {label}")
        buttons.append(
            [InlineKeyboardButton(f"{i + 1}. {label[:60]}", callback_data=t["external_urls"]["spotify"])]
        )

    await msg.edit_text(
        "Select a track to download:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    query = update.callback_query
    await query.answer()
    url = query.data
    await query.edit_message_text(f"Downloading...")
    result = download(url)
    await query.edit_message_text(result)


def main():
    log.info("Starting SpotiFLAC Telegram bot")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("dl", cmd_dl))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
