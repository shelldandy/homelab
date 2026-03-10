#!/usr/bin/env python3
"""
Queries Last.fm top albums for artists recently added to Lidarr (with no monitored albums),
then monitors only those top albums in Lidarr and triggers a search.
"""
import json, os, re, time, logging
import requests

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

LASTFM_API_KEY  = os.environ["LASTFM_API_KEY"]
LIDARR_ENDPOINT = os.environ.get("LIDARR_ENDPOINT", "http://lidarr:8686")
LIDARR_API_KEY  = os.environ["LIDARR_API_KEY"]
TOP_ALBUMS      = int(os.environ.get("TOP_ALBUMS_COUNT", "2"))
STATE_FILE      = os.environ.get("STATE_FILE", "/data/processed_artists.json")
INTERVAL        = int(os.environ.get("SCRIPT_INTERVAL", "3600"))  # seconds
MAX_RETRIES     = int(os.environ.get("MAX_RETRIES", "3"))

def lidarr(method, path, **kwargs):
    url = f"{LIDARR_ENDPOINT}/api/v1{path}"
    headers = {"X-Api-Key": LIDARR_API_KEY}
    r = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()

def lastfm_top_albums(artist_name, mbid=None, limit=20):
    params = {
        "method": "artist.gettopalbums",
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit,
    }
    if mbid:
        params["mbid"] = mbid
    else:
        params["artist"] = artist_name

    r = requests.get("https://ws.audioscrobbler.com/2.0/", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    # Last.fm returns an error object if mbid not found — fall back to name lookup
    if "error" in data:
        log.debug(f"[{artist_name}] Last.fm mbid lookup failed (error {data['error']}), falling back to name")
        params.pop("mbid", None)
        params["artist"] = artist_name
        r = requests.get("https://ws.audioscrobbler.com/2.0/", params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

    return [a["name"] for a in data.get("topalbums", {}).get("album", [])]

def normalize(s):
    s = s.lower()
    s = re.sub(r"\(.*?\)", "", s)   # strip parenthetical suffixes like (Deluxe Edition)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\bthe\b", "", s)
    return s.strip()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            d = json.load(f)
            # handle old format (plain list)
            if isinstance(d, list):
                return set(d), {}
            return set(d["processed"]), d.get("retries", {})
    return set(), {}

def save_state(processed, retries):
    with open(STATE_FILE, "w") as f:
        json.dump({"processed": list(processed), "retries": retries}, f)

def run_once():
    processed, retries = load_state()
    artists = lidarr("GET", "/artist")
    changed = False

    for artist in artists:
        aid = artist["id"]
        name = artist["artistName"]
        mbid = artist.get("foreignArtistId")
        if aid in processed:
            continue

        albums = lidarr("GET", f"/album?artistId={aid}")
        if not albums:
            log.info(f"[{name}] No albums yet in Lidarr, will retry next run")
            continue

        try:
            top_names = lastfm_top_albums(name, mbid=mbid)
        except Exception as e:
            log.warning(f"[{name}] Last.fm error: {e}")
            continue

        log.debug(f"[{name}] Last.fm top: {top_names[:5]}")
        log.debug(f"[{name}] Lidarr albums: {[a['title'] for a in albums[:5]]}")

        top_normalized = [normalize(n) for n in top_names[:TOP_ALBUMS * 4]]
        to_monitor = []
        for album in albums:
            if normalize(album["title"]) in top_normalized:
                to_monitor.append(album)
            if len(to_monitor) >= TOP_ALBUMS:
                break

        if not to_monitor:
            retry_key = str(aid)
            retries[retry_key] = retries.get(retry_key, 0) + 1
            if retries[retry_key] >= MAX_RETRIES:
                sorted_albums = sorted(albums, key=lambda a: a.get("releaseDate", ""), reverse=True)
                to_monitor = sorted_albums[:TOP_ALBUMS]
                log.warning(f"[{name}] No Last.fm match after {MAX_RETRIES} retries — falling back to most recent album(s): {[a['title'] for a in to_monitor]}")
            else:
                log.warning(f"[{name}] No Last.fm top albums matched Lidarr albums (attempt {retries[retry_key]}/{MAX_RETRIES}) — will retry")
                changed = True  # save updated retry count
                continue

        album_ids = []
        for album in to_monitor:
            album["monitored"] = True
            lidarr("PUT", f"/album/{album['id']}", json=album)
            album_ids.append(album["id"])
            log.info(f"[{name}] Monitoring: {album['title']}")

        lidarr("POST", "/command", json={"name": "AlbumSearch", "albumIds": album_ids})
        log.info(f"[{name}] Search triggered for {len(album_ids)} album(s)")

        processed.add(aid)
        changed = True

    if changed:
        save_state(processed, retries)

if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception as e:
            log.error(f"Run failed: {e}")
        time.sleep(INTERVAL)
