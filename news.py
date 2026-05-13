#!/usr/bin/env python3
"""News Clipper CLI — keyword-based news aggregator via Google News RSS.

Outputs headline + link rows to a local .xlsx file (default) or appends to a
Google Sheet (opt-in). Supports Google search operators (AND/OR/quotes/groups),
last-N-days filter, and an optional trusted-source whitelist.

For the multi-query Streamlit UI, see app.py.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from core import (
    dedupe,
    fetch_news,
    filter_trusted,
    load_whitelist,
    write_gsheet,
    write_xlsx,
)

# Windows cp949 콘솔에서도 한글 출력이 깨지지 않도록 stdout/stderr를 UTF-8로 재설정.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Keyword-based news aggregator (Google News RSS → xlsx/gsheet)"
    )
    ap.add_argument(
        "--query",
        required=True,
        help='Google search syntax, e.g. "M&A OR 인수 OR 합병"',
    )
    ap.add_argument("--days", type=int, default=1, help="Last N days (default: 1)")
    ap.add_argument(
        "--trusted-sources",
        help="Path to whitelist file OR comma-separated domain/source list",
    )
    ap.add_argument("--output", choices=["xlsx", "gsheet"], default="xlsx")
    ap.add_argument("--out-path", help="Output .xlsx path (default: news_<timestamp>.xlsx)")
    ap.add_argument("--sheet-id", help="Google Sheet ID (required for --output gsheet)")
    ap.add_argument(
        "--credentials",
        help="Service account JSON path (or set GOOGLE_APPLICATION_CREDENTIALS env)",
    )
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    print(f"[+] Query: {args.query!r}  window: last {args.days}d", file=sys.stderr)
    items = fetch_news(args.query, args.days)
    print(f"[+] Raw items fetched: {len(items)}", file=sys.stderr)

    items = dedupe(items)
    print(f"[+] After dedup: {len(items)}", file=sys.stderr)

    whitelist = load_whitelist(args.trusted_sources)
    if whitelist:
        items = filter_trusted(items, whitelist)
        print(
            f"[+] After trusted-source filter ({len(whitelist)} entries): {len(items)}",
            file=sys.stderr,
        )

    if args.output == "xlsx":
        out = args.out_path or f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        write_xlsx(items, args.query, out)
        print(f"[+] Wrote {len(items)} rows → {out}")
    else:
        if not args.sheet_id:
            sys.exit("--sheet-id is required when --output gsheet")
        creds = args.credentials or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds:
            sys.exit(
                "--credentials path or GOOGLE_APPLICATION_CREDENTIALS env required"
            )
        write_gsheet(items, args.query, args.sheet_id, creds)
        print(f"[+] Appended {len(items)} rows → Google Sheet {args.sheet_id}")


if __name__ == "__main__":
    main()
