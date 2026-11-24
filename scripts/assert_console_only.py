#!/usr/bin/env python3
"""Fail if README's console tables contain a game, accessory, or bundle.

The 2026-11-24 incident: Staples search results included "Forza Motorsport for
Xbox Series X [Disc]" and the table listed it as a console. This guard makes that
regression impossible to merge or auto-commit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CONSOLE_RE = re.compile(r"(xbox\s+series\s+[xs]\b|playstation\s*5\b|\bps5\b)", re.I)
NON_CONSOLE_RE = re.compile(
    r"(forza|nba\b|nhl\b|fifa|madden|spider-?man|\bgame\b|\bjeu\b|controller|manette|"
    r"headset|casque|charging|\bdock\b|accessor|bundle|\blot\b|skin\b|\bcase\b|steelbook)",
    re.I)

README = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")


def main() -> int:
    bad = []
    for ln, line in enumerate(README.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        name = cells[0]
        if name.lower() in ("console", "item", "retailer / store", "---", "") or set(name) <= {"-"}:
            continue
        # Only police rows that claim to be a console-adjacent product.
        if CONSOLE_RE.search(name) and NON_CONSOLE_RE.search(name):
            bad.append((ln, name))
        elif NON_CONSOLE_RE.search(name) and not CONSOLE_RE.search(name):
            # game/accessory row with no console keyword at all
            bad.append((ln, name))
    if bad:
        print("FAIL: non-console rows in console tables:")
        for ln, name in bad:
            print(f"  line {ln}: {name}")
        return 1
    print("OK: no games/accessories in console tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
