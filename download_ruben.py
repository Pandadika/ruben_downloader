#!/usr/bin/env python3
"""
DR Arkivet — Bulk episode downloader
"Ruben - drengen der kan tale med ting"

Requirements:
    uv sync   (requests + imageio-ffmpeg; a system ffmpeg on PATH is used if present)

Usage:
    uv run python download_ruben.py

Episodes are saved as:
    ./ruben_episodes/YYYY-MM-DD_HHmm_NNNN_Ruben.mp3

NOTE: AUTH_TOKEN is sent as a cookie named "Authorization".
      It expires after a while. If you get 401/403 errors:
        1. Open kb.dk in your browser
        2. Network tab → any ds-api request → Request Headers → Cookie
        3. Copy the value of the Authorization= cookie
        4. Paste it as AUTH_TOKEN below and re-run.
      Already-downloaded files are automatically skipped.
"""

import re
import shutil
import subprocess
import sys
import time
import requests
from pathlib import Path
from urllib.parse import urljoin

# ── Configuration ─────────────────────────────────────────────────────────────

AUTH_TOKEN = "uwYZvJY4rqkCh+gdaMxXJUueWoz/wNoBfDZdqvH6QBGOohzwlHqYuYn+0jRPrrHmmyDMqlZYvkGWoNNqtHVm1QFo0xo+YpfNh7c1z37Om0soypePU876nnFnnhZynDqwLZMZQE9Hzw/+n9hzvxF1aHnXmE4OcTCcatAiP9CscIDZf5V2Y8htzFD5ixR2BTlcfT70iMQL5X+tk5Hlro/ZczseFE6uhhbkfVMsmkkGOhRkdAumGRSacZiCPYWU5tTdX7eaiTN64/p68HV+lMQYJEOStLl3yQwIOJvbDNc8cIU2WPGqm/CrIac7oxx/6z2pVBS6PJntPp5OZwqbJJkIGskaZdGpGnwbroRExgpn0g8hDThXz/fCtDYTx/itSBAiVygA2uHkJ70nyqTWyTO+80uut2TzQUxZqfuwB2u2vo2ILixVHfoi7+t2DRESZhyvCw//qhd2Qle0CZ5vEUDW/Whsk8wtp0ccYIl8OJ21p3OCS0iGfLFj94aXAbUC0hBXWpx1SZHVGIsBUuUW12DdZPj3tHZ30aQ7pkpDSrE5u26wHgy7VSvEbWPGlmfIhujVEQQvB89A305Z1GABDMhPN0jVuS+LRK/5ZOwJdkLt73DrWjWrleeF6acrdJV6ZQQVpHFzFonluXh0vKFZyWWK0an6bQMJCYtZCQhugQvUCMDRqozIbnFw7up93Loumgw1K1pGBwy/m3XewIJPivF+c3FZfkPi94PN7+NBM6wwkwzQ7LvfY/NZ7wXdqkHvU9JcksSZ4qfrH3Lm73DacLxL6hC73V2BGm6FYaAw2x+EJkn9BtZIq9GLKdNbhFZSe+XnW2qtK/M+x2TF5tI5t4MA3s6bcKO1ntSHRzE8Bxz2i99s4YXyDQDTGbiekryTE+n+Dfnq3DU1Uq4hWFIn2WvjTzn1FxV4q2yf6AjlCstxky9iNUr3pBw1XXdb6k1zHxCjlbp5qe1VS1QXVT3FZIAY9SmZ50pzicsI9rcsFr7xO85PUXx+ZDLaGdNnU/uf2epk70KCjbcw/WWbTfYrGW62dor7VWiZSdAigsWP+1k+chRcBsmPMsufx3ykMfVNM8rXU8tJWV5MjqC7Z97II2rprYeH1ANAypYTi6D+vMmhsQ2dz9LU1wXfg+dMXy2JmNP07xG9IJA1YE+OgSa0fb8/jn+PlwOYbJvF9rPb3F478o5CYHrvPW1SjyNcj0uRS4HLbqRxIvEfBxloNwyU/VqgIgCv1kLPXrwpqJkipJvTJNJn7iiQFPW6QzNlfEDgnObcsM9l+owLF54HiBCNQvLgRCyXjg8J5ZviR+bdsjsGR8htXhzjjT1ZBB+YhojP0YGJ37TSoLA3DLCAVUFDBOvknpHPSuHJUWwW/6fdYilYHZMXhAGKKvywtchlPjf0XdGNO/kHOV5SJ2EA1mXJKq6wUOyxBvDxoGE/d6HejqirXaBmZtKdu8kJekKdfgIBBjKGiBKOd1baPe32Ekxqh5kONahqIgCjm5Rc6xLeFBYwTqx4D8tvYM13/GZLydJTkfHIGBfqS5lP905YiHKH2xyPALIZ8j7/twg4d3co2/6DeaOqLhFsz2NZbv0irJmMbpgxB661Fgj65l4BB0W3v8+m9wBaw3pgeTDu9el2Q2SoGcpZR+2B/CsiiYfGdQqwVGgn+7mPHdgRV4EnBuJgB125kSVD/Rm4htVGjOuSIO0nDcEfLy66rL+bADCi8fRC1/3vNw=="
AUTH_TOKEN = "nHYfexxvfNU/taShVhuXILgWfAiEiSThSvFpeo+DE1E3jZXJEqnG3BiS6CvUcctlBG5GBXtNkvfZbQcipcyw3Fa3j/Mo/92RhitAjx72LXCnHtvcqHAitajL+bBj+ezhl3DpeetFY3BeltsRj0JqQVx8qD7NSxOlj+BiuLqh8rwNs+BLQc6Dm3D8gHgZ1aLjdFEO2BAh9RECygzAzKwrc2lUocHogimDaLyRu5qngqGG2Tu1akeeCCY89+yeuq6QO48VOb+/H1bkRAUBn7XhIFck2eNnJunk87HqfL/FVziFIz3MMfDYSpBGN3PMqwkmTWKVyVTSvLuKR0AzY+Mbgkujcw8X6Yg4U+nAHkRO8XKFwkT+1I35ItFY/C3KOhFg/ljdW1AjBeGv9qdVIeBformNQgXs3EmXqxo1ZxKLnyG/HXQ7Hcb9nacrG5y8AoA7zN0U3QGds5RJA8f3gO7R4cwGne+pdFcsWq1s42XKOoub0LcjS98t3YxQvTl6yq0yEslu8G4LRdZ/iU27gzICBWSSHGL3qeHBkgq+uxkMgxWEkJfaBf+HhlwLP3pSDVc+OWjBcaRUzSDDpJCMTk748NiEtNo+mJd2S3ROGBWPutOa/+120CU/HpjIbcHQxw86Z5LumyDjIbO8G6R67W7ZshNCVbCm7vOptGOlywVX8fyE3b2QxKvn3Xsphs2e2F+Aap7oqK69wnmppjYfVvh9bfSmLUykbr1eIDbWzw5QeGpbfZLvHGovpzsPmtJH+Eh4+OZql3gIThbQ/YDEObOHM1sNZ8nQEorwFuUelwBfthJOf7lzcXaOOpz05NvPrSHtxQ6AUGHR0aUvwno/aBxFUjI4dUb+6cqwx6AKEJSMwLtKm8tfX4+/mJmD5gVS22zK3SVcQxUPaIWP6nqkNRVFLo0IDIG0X0VFR66fbuXTTz114daWVY5mOOj+3h5gP0Q3Hat7gpK6MFY5OW7kMJuqtvJ2Vw056xvn8z2sYMSTuxoZqtSj8EmxGuAdBwKQCptTwTW4L6y/Hs0ZKYaSD+lt/IJVtzV+OEyipjh8CYfyzCw2RVtQBGaA8h8XHe5SUaHCRjEGfTfhBJQoozT1LA5nLG1OzKihaCrOd3/N8+cHBGcZ6iyQVcp0Klm72bg47vyelAvuB0o2wCOn1eMbrqhB6wS74UyKRvcg7Z0vphvyD5VqltqG6WDj6UREWP8MFXaBg3gy01oS695dN62ICPGSEqBMdTyqW1/q8GLnQagy0q9BVi8PkvHGTB1uuXR7XHbKVq1Drv4ybFHR7LdEg4XbgT2QSBMwh9ePCFCc5Tyi4MUSBaQ64GBb73yZijYDfR+EyzgNrNXNKzCDx/kyuaEaMUOYB8uv1731Q2uvQE0ftma99+PvJlEC9hnAjYcK5dM4vNRwEZeivS590fu1ipCxc8PWzOVq8mkzAMJKg0hRks2aWkP0QRsaSneflXdWED8Km98wk4imbM1cZf1RylzWO+VOYG2zeDFuGES3faQsh0lp1n1MlC/bZE8ZM8m0oIvfVCRaL2lMU5l10PhGihCXsrCTapH5g2HN7/dCMqIlwv7mHmnhgJ1ZMpiJHN8Xag/iJs97kwqhcdYGdhUzu3tK7Y/ZLk+5nZTmAKDa4V9RSuTbxumcVhbosLNcC2i8OhFR356XPzxbkb3NsrwsfuaTcuAgcfKmaz5yfCqy+wXmGVVv66BmLbnByVM3N20WKkti/w=="
SEARCH_URL   = "https://www.kb.dk/ds-api/bff/v1/proxy/search/"
RECORD_URL   = "https://www.kb.dk/ds-api/bff/v1/proxy/record/{record_id}?format=JSON-LD"
# The CDN no longer serves whole-file downloads (serveFlavor → 403), but the
# HLS stream of the same flavor is open. We fetch the HLS manifest and let
# ffmpeg transcode the AAC segments to a proper MP3.
MANIFEST_URL = (
    "https://api.kltr.nordu.net/p/397/sp/39700/playManifest"
    "/entryId/{entry_id}/format/applehttp/protocol/https"
)

SEARCH_QUERY = '"Ruben - drengen der kan tale med ting"'
PAGE_SIZE    = 50
OUTPUT_DIR   = Path("ruben_episodes")
DELAY        = 0.4   # seconds between API calls — be polite to the server

# ── Session ───────────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; research-downloader)",
    "Referer":    "https://www.kb.dk/",
})
session.cookies.set("Authorization", AUTH_TOKEN, domain="www.kb.dk")

# ── Helpers ───────────────────────────────────────────────────────────────────

def search_page(start: int) -> dict:
    r = session.get(SEARCH_URL, params={
        "q":    SEARCH_QUERY,
        "sort": "startTime asc",
        "start": start,
        "rows": PAGE_SIZE,
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def get_record(record_id: str) -> dict:
    url = RECORD_URL.format(record_id=requests.utils.quote(record_id, safe=""))
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def extract_kaltura_id(record: dict) -> str | None:
    for item in record.get("identifier", []):
        if isinstance(item, dict) and item.get("PropertyID") == "KalturaID":
            return item.get("value")
    return None


def make_filename(start_time: str, idx: int) -> str:
    """'2002-01-02T05:50:00Z'  →  '2002-01-02_0550_0001_Ruben.mp3'"""
    m = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})", start_time or "")
    if m:
        return f"{m.group(1)}_{m.group(2)}{m.group(3)}_{idx:04d}_Ruben.mp3"
    return f"0000-00-00_0000_{idx:04d}_Ruben.mp3"


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found — install it or `uv add imageio-ffmpeg`")


FFMPEG = find_ffmpeg()


def resolve_hls_url(entry_id: str) -> str:
    """playManifest returns an #EXTM3U master playlist; take its first variant."""
    url = MANIFEST_URL.format(entry_id=entry_id)
    r = session.get(url, timeout=30)
    r.raise_for_status()
    for line in r.text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return urljoin(url, line)
    raise RuntimeError("no variant stream in HLS master playlist")


def download_mp3(entry_id: str, dest: Path) -> bool:
    tmp = dest.with_suffix(".part")
    try:
        hls_url = resolve_hls_url(entry_id)
        subprocess.run(
            [FFMPEG, "-v", "error", "-y",
             "-i", hls_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "160k",
             "-f", "mp3", str(tmp)],
            check=True, capture_output=True, timeout=600,
        )
        tmp.rename(dest)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ ffmpeg error: {e.stderr.decode(errors='replace').strip()}")
    except Exception as e:
        print(f"  ✗ download error: {e}")
    tmp.unlink(missing_ok=True)
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ── Step 1: collect all episode records via paginated search ──────────────
    print("Fetching episode list from KB search API …\n")
    all_docs, start = [], 0

    while True:
        try:
            data = search_page(start)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            print(f"✗ Search HTTP {code} at start={start}")
            if code in (401, 403):
                print("  → Token expired. Get a fresh one from your browser's Network tab.")
            break
        except Exception as e:
            print(f"✗ Search error: {e}")
            break

        # Solr-style: {"response": {"numFound": N, "docs": [...]}}
        resp  = data.get("response", {})
        docs  = resp.get("docs", [])
        total = resp.get("numFound", 0)

        if not docs:
            print(f"No docs in response. Keys seen: {list(data.keys())}")
            if resp:
                print(f"  response keys: {list(resp.keys())}")
            break

        all_docs.extend(docs)
        print(f"  {len(all_docs):>4} / {total} collected …", end="\r")

        start += PAGE_SIZE
        if start >= total:
            break
        time.sleep(DELAY)

    total_found = len(all_docs)
    print(f"\n\nFound {total_found} episodes in total.\n")
    if not total_found:
        return

    # ── Step 2: resolve KalturaID and download each episode ───────────────────
    downloaded, skipped, failed = 0, 0, 0

    for idx, doc in enumerate(all_docs, start=1):
        record_id  = doc.get("id", "")
        start_time = doc.get("startTime", "")
        filename   = make_filename(start_time, idx)
        dest       = OUTPUT_DIR / filename

        prefix = f"[{idx:04d}/{total_found}]"

        if dest.exists():
            print(f"{prefix} SKIP  {filename}")
            skipped += 1
            continue

        print(f"{prefix} {filename} … ", end="", flush=True)

        # Fetch JSON-LD record to get KalturaID
        try:
            record     = get_record(record_id)
            kaltura_id = extract_kaltura_id(record)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            print(f"✗ record {code}")
            if code in (401, 403):
                print("  → Token expired. Refresh and re-run (progress is saved).")
                break
            failed += 1
            time.sleep(DELAY)
            continue
        except Exception as e:
            print(f"✗ {e}")
            failed += 1
            time.sleep(DELAY)
            continue

        if not kaltura_id:
            print("✗ no KalturaID in record")
            failed += 1
            time.sleep(DELAY)
            continue

        # Download the MP3
        ok = download_mp3(kaltura_id, dest)
        if ok:
            kb = dest.stat().st_size // 1024
            print(f"✓  {kb} KB")
            downloaded += 1
        else:
            failed += 1

        time.sleep(DELAY)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Downloaded : {downloaded}
  Skipped    : {skipped}  (already existed)
  Failed     : {failed}
  Saved to   : {OUTPUT_DIR.resolve()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")


if __name__ == "__main__":
    main()
