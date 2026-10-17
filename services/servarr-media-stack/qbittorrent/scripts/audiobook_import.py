#!/usr/bin/env python3
"""
qBittorrent Post-Processing Import Hook for Audiobookshelf
Hardlinks completed audiobooks and ebooks into the Audiobookshelf library
and triggers an immediate library scan.
"""
import sys
import os
import json
import logging
import urllib.request
import urllib.error

CONFIG_PATHS = [
    "/config/scripts/audiobook_import.conf",
    "/docker/servarr/qbittorrent/scripts/audiobook_import.conf",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "audiobook_import.conf")
]

conf = {}
for p in CONFIG_PATHS:
    if os.path.exists(p):
        try:
            with open(p, "r") as f:
                conf = json.load(f)
            break
        except Exception:
            pass

LOG_FILE = conf.get("log_file", "/config/logs/audiobook_import.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("audiobook_import")

EXCLUDED_CATEGORIES = {"radarr", "sonarr", "lidarr"}
AUDIO_EXTENSIONS = {".m4b", ".mp3", ".flac", ".m4a", ".aac", ".opus", ".ogg"}
EBOOK_EXTENSIONS = {".epub", ".pdf"}
COMPANION_EXTENSIONS = {".jpg", ".jpeg", ".png", ".cue", ".nfo", ".opf"}
ALL_VALID_EXTENSIONS = AUDIO_EXTENSIONS | EBOOK_EXTENSIONS | COMPANION_EXTENSIONS

def main():
    if len(sys.argv) < 4:
        logger.warning(f"Insufficient arguments: {sys.argv}")
        sys.exit(0)

    torrent_name = sys.argv[1].strip()
    category = sys.argv[2].strip().lower()
    content_path = sys.argv[3].strip()

    logger.info(f"Processing finished torrent: '{torrent_name}' | Category: '{category}' | Path: '{content_path}'")

    if category in EXCLUDED_CATEGORIES:
        logger.info(f"Skipping excluded category: '{category}'")
        sys.exit(0)

    if not os.path.exists(content_path):
        logger.warning(f"Content path does not exist: '{content_path}'")
        sys.exit(0)

    files_to_link = []
    has_audio_or_book = False

    if os.path.isfile(content_path):
        ext = os.path.splitext(content_path)[1].lower()
        if ext in AUDIO_EXTENSIONS or ext in EBOOK_EXTENSIONS:
            has_audio_or_book = True
            files_to_link.append((content_path, os.path.basename(content_path)))
    elif os.path.isdir(content_path):
        for root, _, files in os.walk(content_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in AUDIO_EXTENSIONS or ext in EBOOK_EXTENSIONS:
                    has_audio_or_book = True
                if ext in ALL_VALID_EXTENSIONS:
                    full_src = os.path.join(root, file)
                    rel_path = os.path.relpath(full_src, content_path)
                    files_to_link.append((full_src, rel_path))

    if not has_audio_or_book:
        logger.info(f"No audiobooks or books found in '{torrent_name}'. Skipping.")
        sys.exit(0)

    library_target = conf.get("library_target", "/data/books/audiobooks")
    target_dir = os.path.join(library_target, torrent_name)
    os.makedirs(target_dir, exist_ok=True)

    linked_count = 0
    for src, rel in files_to_link:
        dst = os.path.join(target_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            try:
                os.link(src, dst)
                linked_count += 1
                logger.info(f"Hardlinked: {rel}")
            except Exception as e:
                logger.error(f"Failed to hardlink {src} -> {dst}: {e}")
        else:
            logger.info(f"Already exists at destination: {rel}")

    logger.info(f"Imported {linked_count} files into '{target_dir}'.")

    # Trigger Audiobookshelf Scan
    base_url = conf.get("abs_base_url")
    library_id = conf.get("abs_library_id")
    api_token = conf.get("abs_api_token")

    if base_url and library_id and api_token:
        scan_url = f"{base_url.rstrip('/')}/api/libraries/{library_id}/scan"
        logger.info(f"Triggering Audiobookshelf library scan: {scan_url}")
        try:
            req = urllib.request.Request(
                scan_url,
                data=b"{}",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"Audiobookshelf scan triggered successfully (HTTP {resp.status})")
        except Exception as e:
            logger.error(f"Failed to trigger Audiobookshelf scan: {e}")
    else:
        logger.warning("Audiobookshelf credentials not configured; skipping scan trigger.")

if __name__ == "__main__":
    main()
