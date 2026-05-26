#!/usr/bin/env python3
"""Example client for MiMo Multilang Bridge.

Usage:
    python examples/client.py translate "Hello world" --to id
    python examples/client.py summarize @path/to/doc.txt --max-bullets 5
    python examples/client.py extract "Invoice 4500 RMB due 2026-06-15"
"""
from __future__ import annotations

import argparse
import json
import sys

import httpx

DEFAULT_BASE = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="MiMo Multilang Bridge client")
    parser.add_argument("verb", choices=["translate", "summarize", "extract", "synthesize", "stats"])
    parser.add_argument("text", nargs="?", default="", help="Text or @file path")
    parser.add_argument("--to", default="id", help="Target language: id|en|zh")
    parser.add_argument("--from", dest="src", default="auto", help="Source language hint")
    parser.add_argument("--max-bullets", type=int, default=7)
    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()

    text = args.text
    if text.startswith("@"):
        with open(text[1:], encoding="utf-8") as fh:
            text = fh.read()

    body = {"text": text, "to": args.to, "from": args.src, "max_bullets": args.max_bullets}

    if args.verb == "stats":
        r = httpx.get(f"{args.base}/api/stats", timeout=10)
    else:
        r = httpx.post(f"{args.base}/api/{args.verb}", json=body, timeout=120)

    r.raise_for_status()
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
