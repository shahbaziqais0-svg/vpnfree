
import html
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources.txt"
OUTPUT = ROOT / "subscription.txt"

PROTOCOLS = (
    "vless", "vmess", "trojan", "ss",
    "ssr", "tuic", "hysteria", "hysteria2",
    "hy2", "socks", "wireguard", "wg",
    "anytls", "naive"
)

pattern = re.compile(
    r"(?:" + "|".join(PROTOCOLS) + r")://[^\s<>\"']+",
    re.IGNORECASE,
)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; HiddifySubBot/1.0)"
})

configs = []
seen = set()

channels = [
    line.strip().lstrip("@")
    for line in SOURCES.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
]

for channel in channels:
    url = f"https://t.me/s/{channel}"
    print(f"Reading {channel}...")

    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Read visible text and link destinations.
        texts = [soup.get_text(" ", strip=True)]
        texts.extend(
            a.get("href", "")
            for a in soup.find_all("a", href=True)
        )

        for text in texts:
            text = html.unescape(text)

            for match in pattern.findall(text):
                config = match.rstrip(".,;)")
                if config not in seen:
                    seen.add(config)
                    configs.append(config)

    except requests.RequestException as exc:
        print(f"Could not read {channel}: {exc}")

    time.sleep(2)

if not configs:
    # Preserve the last good subscription instead of replacing it
    # with an empty file when Telegram is unavailable.
    print("No configs found; preserving previous output.")
    raise SystemExit(1)

OUTPUT.write_text(
    "\n".join(configs) + "\n",
    encoding="utf-8",
)

print(f"Saved {len(configs)} unique configs.")
