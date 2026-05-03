#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


TOC_START = "<!-- TOC START -->"
TOC_END = "<!-- TOC END -->"

ATX_HEADER_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<hashes>#{1,6})[ \t]+(?P<title>.*?)(?:[ \t]+#*)?[ \t]*$"
)

FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)?$")


@dataclass
class Header:
    level: int
    title: str
    anchor: str


def strip_md_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)     # link
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)    # image
    text = re.sub(r"`([^`]+)`", r"\1", text)                 # inline code
    text = text.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def github_slugify(text: str) -> str:
    text = strip_md_inline(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9 \-]", "", text)
    text = text.replace(" ", "-")
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def _safe_stdout_write(s: str) -> None:
    """
    Windows: gdy stdout jest w cp1250/cp852 itp., wypisanie Unicode potrafi wywalić.
    Tu wymuszamy zapis UTF-8 na bufor binarny stdout.
    """
    data = s.encode("utf-8", errors="replace")
    try:
        sys.stdout.buffer.write(data)
    except Exception:
        # fallback (np. gdy ktoś odpala w środowisku bez .buffer)
        sys.stdout.write(s)


def extract_headers(md: str, ignore_code: bool, min_level: int, max_level: int) -> List[Tuple[int, str]]:
    headers: List[Tuple[int, str]] = []

    in_fence = False
    fence_marker: Optional[str] = None  # ``` albo ~~~
    fence_len: int = 0

    for line in md.splitlines():
        # 1) Wcięty blok kodu (4 spacje lub tab) — potraktuj jako kod i ignoruj nagłówki
        if ignore_code and (line.startswith("    ") or line.startswith("\t")):
            continue

        # 2) Bloki fenced: ``` lub ~~~ (dowolna długość >= 3)
        m_fence = FENCE_START_RE.match(line)
        if ignore_code and m_fence:
            marker = m_fence.group("fence")[0]  # ` lub ~
            length = len(m_fence.group("fence"))

            if not in_fence:
                in_fence = True
                fence_marker = marker
                fence_len = length
            else:
                # zamykamy tylko jeśli marker jest ten sam i długość >= otwierającej
                if fence_marker == marker and length >= fence_len:
                    in_fence = False
                    fence_marker = None
                    fence_len = 0
            continue

        if ignore_code and in_fence:
            continue

        # 3) Nagłówki
        m = ATX_HEADER_RE.match(line)
        if not m:
            continue

        level = len(m.group("hashes"))
        if level < min_level or level > max_level:
            continue

        title = m.group("title").strip()
        if not title:
            continue

        headers.append((level, title))

    return headers


def make_unique_anchors(headers: List[Tuple[int, str]]) -> List[Header]:
    used: Dict[str, int] = {}
    result: List[Header] = []

    for level, title in headers:
        base = github_slugify(title) or "section"

        if base not in used:
            used[base] = 0
            anchor = base
        else:
            used[base] += 1
            anchor = f"{base}-{used[base]}"

        result.append(Header(level=level, title=strip_md_inline(title), anchor=anchor))

    return result


def render_toc(headers: List[Header], bullets: str) -> str:
    if not headers:
        return ""

    lines: List[str] = []
    base_level = min(h.level for h in headers)

    for h in headers:
        indent = "  " * (h.level - base_level)
        lines.append(f"{indent}{bullets} [{h.title}](#{h.anchor})")

    return "\n".join(lines) + "\n"


def upsert_toc(original: str, toc_body: str) -> str:
    block = f"{TOC_START}\n\n{toc_body}\n{TOC_END}\n"

    if TOC_START in original and TOC_END in original:
        pattern = re.compile(re.escape(TOC_START) + r".*?" + re.escape(TOC_END), re.DOTALL)
        return pattern.sub(lambda _: block.strip("\n"), original, count=1).rstrip() + "\n"

    return (block + "\n" + original.lstrip("\n")).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Ścieżka do pliku .md")
    ap.add_argument("--inplace", action="store_true", help="Wstaw/zaaktualizuj TOC w pliku")
    ap.add_argument("--max-level", type=int, default=6)
    ap.add_argument("--min-level", type=int, default=1)
    ap.add_argument("--bullets", choices=["-", "*"], default="-")
    ap.add_argument(
        "--no-code-ignore",
        action="store_true",
        help="Nie ignoruj nagłówków w blokach kodu (domyślnie są ignorowane)",
    )
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print(f"Nie znaleziono pliku: {args.file}", file=sys.stderr)
        return 2

    md = open(args.file, "r", encoding="utf-8").read()

    headers_raw = extract_headers(
        md,
        ignore_code=(not args.no_code_ignore),
        min_level=args.min_level,
        max_level=args.max_level,
    )
    headers = make_unique_anchors(headers_raw)
    toc = render_toc(headers, bullets=args.bullets)

    if not toc:
        print("Brak nagłówków do wygenerowania TOC.", file=sys.stderr)
        return 1

    if args.inplace:
        updated = upsert_toc(md, toc.rstrip("\n"))
        with open(args.file, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        return 0

    _safe_stdout_write(toc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())