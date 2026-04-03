#!/usr/bin/env python3
"""YouTube Research Tool - searches YouTube and returns structured metadata via yt-dlp."""

import argparse
import json
import sys

import yt_dlp


def search_youtube(query, max_results=25):
    """Search YouTube for videos matching query and return metadata."""

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "default_search": f"ytsearch{max_results}",
        "ignoreerrors": True,
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        if not info or "entries" not in info:
            return results

        for entry in info["entries"]:
            if entry is None:
                continue
            results.append(
                {
                    "title": entry.get("title", "N/A"),
                    "url": entry.get("webpage_url") or entry.get("url", "N/A"),
                    "author": entry.get("uploader") or entry.get("channel", "N/A"),
                    "views": entry.get("view_count", 0),
                    "duration_seconds": entry.get("duration", 0),
                    "duration_string": entry.get("duration_string", "N/A"),
                    "upload_date": entry.get("upload_date", "N/A"),
                    "description": (entry.get("description") or "")[:300],
                }
            )

    return results


def main():
    parser = argparse.ArgumentParser(description="Search YouTube and return video metadata as JSON.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("-n", "--max-results", type=int, default=25, help="Number of results (default 25)")
    parser.add_argument("--urls-only", action="store_true", help="Output only URLs, one per line")
    args = parser.parse_args()

    results = search_youtube(args.query, args.max_results)

    if args.urls_only:
        for r in results:
            print(r["url"])
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
