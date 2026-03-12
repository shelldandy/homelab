#!/usr/bin/env python3
"""
Watches discoverylastfm container logs for failed album additions,
then searches slskd for those albums and enqueues downloads to music-inbox.
"""
import json, os, re, time, logging
import requests
import docker

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SLSKD_ENDPOINT       = os.environ.get("SLSKD_ENDPOINT", "http://slskd:5030")
SLSKD_API_KEY        = os.environ["SLSKD_API_KEY"]
DOWNLOAD_DIR         = os.environ.get("DOWNLOAD_DIR", "/share/media/music-inbox")
STATE_FILE           = os.environ.get("STATE_FILE", "/data/processed.json")
SEARCH_TIMEOUT       = int(os.environ.get("SEARCH_TIMEOUT", "30"))
MIN_FILE_MATCH_RATIO = float(os.environ.get("MIN_FILE_MATCH_RATIO", "0.8"))
CONTAINER_NAME       = os.environ.get("DISCOVERYLASTFM_CONTAINER", "discoverylastfm")

ALLOWED_EXTENSIONS = {".flac", ".mp3"}

# Regex patterns for log lines
RE_ARTIST = re.compile(r"Processo artista simile:\s+(.+?)\s+\(([0-9a-f-]+)\)", re.IGNORECASE)
RE_FAILED = re.compile(r"Failed to add album\s+(.+)", re.IGNORECASE)


def normalize(s):
    s = s.lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\bthe\b", "", s)
    return s.strip()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(tuple(x) for x in data)
            return set(tuple(x) for x in data.get("processed", []))
    return set()


def save_state(processed):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"processed": [list(x) for x in processed]}, f)


def slskd_search(query):
    """POST a search to slskd, poll until complete, return responses."""
    headers = {"X-API-Key": SLSKD_API_KEY, "Content-Type": "application/json"}
    r = requests.post(
        f"{SLSKD_ENDPOINT}/api/v0/searches",
        headers=headers,
        json={"searchText": query},
        timeout=15,
    )
    r.raise_for_status()
    search_id = r.json()["id"]

    deadline = time.time() + SEARCH_TIMEOUT
    while time.time() < deadline:
        time.sleep(3)
        r = requests.get(
            f"{SLSKD_ENDPOINT}/api/v0/searches/{search_id}",
            headers=headers,
            params={"includeResponses": "true"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("isComplete"):
            return data.get("responses", [])

    log.warning(f"Search timed out after {SEARCH_TIMEOUT}s for query: {query}")
    return []


def pick_best_response(responses, album_title):
    """
    Select the response (user) with the most matching audio files.
    Prefer FLAC. Skip responses with only disallowed extensions.
    Returns (username, files_list) or (None, []).
    """
    norm_album = normalize(album_title)
    best_username = None
    best_files = []
    best_score = 0

    for response in responses:
        username = response.get("username")
        files = response.get("files", [])

        audio_files = [
            f for f in files
            if os.path.splitext(f.get("filename", "").lower())[1] in ALLOWED_EXTENSIONS
        ]
        if not audio_files:
            continue

        flac_count = sum(
            1 for f in audio_files
            if f.get("filename", "").lower().endswith(".flac")
        )
        score = flac_count * 2 + len(audio_files)

        if score > best_score:
            best_score = score
            best_username = username
            best_files = audio_files

    return best_username, best_files


def enqueue_downloads(username, files):
    """POST each file to slskd transfers API."""
    headers = {"X-API-Key": SLSKD_API_KEY, "Content-Type": "application/json"}
    queued = 0
    for f in files:
        payload = {
            "filename": f["filename"],
            "size": f.get("size", 0),
            "token": f.get("token"),
        }
        try:
            r = requests.post(
                f"{SLSKD_ENDPOINT}/api/v0/transfers/downloads/{username}",
                headers=headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            queued += 1
        except requests.HTTPError as e:
            log.warning(f"Failed to queue {f['filename']}: {e}")
    return queued


def handle_failed_album(artist, album, processed):
    key = (normalize(artist), normalize(album))
    if key in processed:
        log.debug(f"[{artist} / {album}] already processed, skipping")
        return

    log.info(f"[{artist} / {album}] search triggered")
    query = f"{artist} {album}"

    try:
        responses = slskd_search(query)
    except Exception as e:
        log.error(f"[{artist} / {album}] slskd search error: {e}")
        return

    if not responses:
        log.warning(f"[{artist} / {album}] no results from slskd")
        processed.add(key)
        save_state(processed)
        return

    username, files = pick_best_response(responses, album)
    if not files:
        log.warning(f"[{artist} / {album}] no usable audio files in results")
        processed.add(key)
        save_state(processed)
        return

    queued = enqueue_downloads(username, files)
    log.info(f"[{artist} / {album}] queued {queued} files from {username}")

    processed.add(key)
    save_state(processed)


def tail_logs(processed):
    """Connect to Docker, tail discoverylastfm logs, parse and act."""
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        log.error(f"Container '{CONTAINER_NAME}' not found, retrying in 60s")
        time.sleep(60)
        return

    log.info(f"Tailing logs from container: {CONTAINER_NAME}")
    current_artist = None

    try:
        for raw_line in container.logs(stream=True, follow=True, tail=0):
            line = raw_line.decode("utf-8", errors="replace").strip()

            m = RE_ARTIST.search(line)
            if m:
                current_artist = m.group(1).strip()
                log.debug(f"Current artist: {current_artist}")
                continue

            m = RE_FAILED.search(line)
            if m and current_artist:
                album_title = m.group(1).strip()
                handle_failed_album(current_artist, album_title, processed)

    except Exception as e:
        log.error(f"Log stream error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    processed = load_state()
    log.info("discoverylastfm-slskd-fallback started")
    while True:
        try:
            tail_logs(processed)
        except Exception as e:
            log.error(f"Outer loop error: {e}")
            time.sleep(15)
