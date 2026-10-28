#!/usr/bin/env python3
"""Hent de sange du streamer på Spotify og gem dem i en CSV-fil.

Bruger Spotify Web API (via spotipy) til at hente:
  * de seneste afspillede numre (max 50 pr. kald - en API-begrænsning)
  * det nummer der afspilles lige nu

Kør med --watch for løbende at logge alt hvad du lytter til, så du
opbygger en komplet historik over tid.

Opsætning: se README.md i samme mappe.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:
    sys.exit("Mangler spotipy - kør: pip install -r requirements.txt")

SCOPES = "user-read-recently-played user-read-currently-playing"
FIELDS = ["played_at", "track", "artists", "album", "duration_ms", "track_id", "url"]


def get_client():
    missing = [v for v in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET") if not os.getenv(v)]
    if missing:
        sys.exit(f"Sæt miljøvariablerne: {', '.join(missing)} (se README.md)")
    auth = SpotifyOAuth(
        scope=SCOPES,
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
        cache_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache"),
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth)


def track_to_row(track, played_at):
    return {
        "played_at": played_at,
        "track": track["name"],
        "artists": ", ".join(a["name"] for a in track["artists"]),
        "album": track["album"]["name"],
        "duration_ms": track["duration_ms"],
        "track_id": track["id"],
        "url": track["external_urls"].get("spotify", ""),
    }


def fetch_recently_played(sp):
    """Returnerer op til 50 senest afspillede numre, ældste først."""
    result = sp.current_user_recently_played(limit=50)
    rows = [track_to_row(item["track"], item["played_at"]) for item in result["items"]]
    return sorted(rows, key=lambda r: r["played_at"])


def fetch_now_playing(sp):
    current = sp.current_user_playing_track()
    if not current or not current.get("item") or current.get("currently_playing_type") != "track":
        return None
    row = track_to_row(current["item"], datetime.now(timezone.utc).isoformat())
    row["is_playing"] = current["is_playing"]
    row["progress_ms"] = current.get("progress_ms") or 0
    return row


def load_seen(path):
    """Læs eksisterende played_at-tidsstempler så vi undgår dubletter."""
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {row["played_at"] for row in csv.DictReader(f)}


def append_rows(path, rows):
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def save_new(sp, path, seen):
    rows = [r for r in fetch_recently_played(sp) if r["played_at"] not in seen]
    if rows:
        append_rows(path, rows)
        seen.update(r["played_at"] for r in rows)
    return rows


def print_rows(rows):
    for r in rows:
        ts = datetime.fromisoformat(r["played_at"].replace("Z", "+00:00")).astimezone()
        print(f"{ts:%Y-%m-%d %H:%M}  {r['artists']} - {r['track']}")


def main():
    parser = argparse.ArgumentParser(description="Hent dine Spotify-afspilninger.")
    parser.add_argument("-o", "--output", default="spotify_history.csv",
                        help="CSV-fil der gemmes i (default: %(default)s)")
    parser.add_argument("--now", action="store_true",
                        help="Vis kun hvad der spiller lige nu")
    parser.add_argument("--watch", action="store_true",
                        help="Bliv ved med at logge nye afspilninger")
    parser.add_argument("--interval", type=int, default=600,
                        help="Sekunder mellem tjek i --watch (default: %(default)s)")
    args = parser.parse_args()

    sp = get_client()

    if args.now:
        row = fetch_now_playing(sp)
        if row is None:
            print("Der afspilles ikke noget lige nu.")
        else:
            state = "Spiller" if row["is_playing"] else "På pause"
            pos = row["progress_ms"] // 1000
            print(f"{state}: {row['artists']} - {row['track']} ({row['album']}) "
                  f"[{pos // 60}:{pos % 60:02d}]")
        return

    seen = load_seen(args.output)
    new = save_new(sp, args.output, seen)
    print_rows(new)
    print(f"{len(new)} nye afspilninger gemt i {args.output}")

    if not args.watch:
        return

    # Endpointet returnerer kun de seneste 50 numre, så et interval på
    # 10 minutter er rigeligt til ikke at miste noget.
    print(f"Overvåger hvert {args.interval}. sekund - stop med Ctrl+C")
    try:
        while True:
            time.sleep(args.interval)
            try:
                new = save_new(sp, args.output, seen)
            except spotipy.SpotifyException as e:
                print(f"API-fejl, prøver igen senere: {e}", file=sys.stderr)
                continue
            print_rows(new)
    except KeyboardInterrupt:
        print("\nStoppet.")


if __name__ == "__main__":
    main()
