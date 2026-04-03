#!/usr/bin/env python3
"""
Full Research Pipeline: YouTube Search -> NotebookLM Analysis -> Infographic
Run this on your local machine where notebooklm login was completed.

Usage:
    python run_pipeline.py "Investment In Saudi Arabia" --count 25
"""

import argparse
import asyncio
import json
import os
import sys
import time

try:
    import yt_dlp
except ImportError:
    sys.exit("ERROR: yt-dlp not installed. Run:  pip install yt-dlp")

try:
    from notebooklm import NotebookLMClient
except ImportError:
    sys.exit('ERROR: notebooklm-py not installed. Run:  pip install "notebooklm-py[browser]"')


def search_youtube(query, max_results=25):
    print(f"\n{'='*60}")
    print(f"  STEP 1: Searching YouTube for {max_results} videos")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        if not info or "entries" not in info:
            print("  No results found!")
            return results

        for i, entry in enumerate(info["entries"], 1):
            if entry is None:
                continue
            video = {
                "title": entry.get("title", "N/A"),
                "url": entry.get("webpage_url") or entry.get("url", "N/A"),
                "author": entry.get("uploader") or entry.get("channel", "N/A"),
                "views": entry.get("view_count", 0),
                "duration_string": entry.get("duration_string", "N/A"),
            }
            results.append(video)
            views = f"{video['views']:,}" if video['views'] else "N/A"
            print(f"  {i:2}. {video['title'][:70]}")
            print(f"      Author: {video['author']}  |  Views: {views}  |  Duration: {video['duration_string']}")
            print(f"      URL: {video['url']}")
            print()

    print(f"  Found {len(results)} videos.\n")
    return results


async def setup_notebook(topic, urls):
    print(f"\n{'='*60}")
    print(f"  STEP 2: Creating NotebookLM notebook and adding sources")
    print(f"{'='*60}\n")

    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(f"Research: {topic}")
        notebook_id = nb.id
        print(f"  Notebook created: {notebook_id}")
        print(f"  Name: Research: {topic}\n")

        success_count = 0
        for i, url in enumerate(urls, 1):
            try:
                print(f"  Adding source {i}/{len(urls)}: {url[:80]}...")
                await client.sources.add_url(notebook_id, url, wait=True)
                success_count += 1
                print(f"    Added successfully")
            except Exception as e:
                print(f"    Error: {e}")

        print(f"\n  Added {success_count}/{len(urls)} sources to notebook.\n")
        return notebook_id


async def get_analysis(notebook_id):
    print(f"\n{'='*60}")
    print(f"  STEP 3: Requesting analysis from NotebookLM")
    print(f"{'='*60}\n")

    async with await NotebookLMClient.from_storage() as client:
        question = (
            "Analyze all the sources and provide a comprehensive summary of the "
            "top findings about investment in Saudi Arabia. Include: "
            "1) Key investment sectors and opportunities, "
            "2) Major trends and developments, "
            "3) Risks and challenges, "
            "4) Notable projects and initiatives (e.g., Vision 2030, NEOM, PIF), "
            "5) Recommendations for investors."
        )
        print(f"  Asking: {question[:100]}...\n")
        result = await client.chat.ask(notebook_id, question)
        print(f"  ANALYSIS:\n")
        print(f"  {result.answer}\n")
        return result.answer


async def generate_infographic(notebook_id, output_dir):
    print(f"\n{'='*60}")
    print(f"  STEP 4: Generating chalkboard-style infographic")
    print(f"{'='*60}\n")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "saudi_investment_infographic.png")

    async with await NotebookLMClient.from_storage() as client:
        print("  Generating infographic (this may take a minute)...")
        status = await client.artifacts.generate_infographic(
            notebook_id,
            instructions="Create in a handwritten chalkboard style with chalk-like text and illustrations",
            orientation="portrait",
        )
        print(f"  Task ID: {status.task_id}")
        print("  Waiting for completion...")
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        print("  Infographic generated!")

        print(f"  Downloading to {output_path}...")
        await client.artifacts.download_infographic(notebook_id, output_path)
        print(f"  Downloaded to: {output_path}\n")
        return output_path


async def run_pipeline(topic, count, output_dir):
    start = time.time()

    print("\n" + "=" * 60)
    print("  RESEARCH PIPELINE: YouTube -> NotebookLM -> Infographic")
    print("=" * 60)
    print(f"  Topic: {topic}")
    print(f"  Videos: {count}")
    print(f"  Output: {output_dir}")

    videos = search_youtube(topic, count)
    if not videos:
        sys.exit("No videos found. Try a different search query.")

    os.makedirs(output_dir, exist_ok=True)
    meta_path = os.path.join(output_dir, "youtube_results.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    print(f"  Video metadata saved to: {meta_path}")

    urls = [v["url"] for v in videos]
    notebook_id = await setup_notebook(topic, urls)

    with open(os.path.join(output_dir, "notebook_id.txt"), "w") as f:
        f.write(notebook_id)

    analysis = await get_analysis(notebook_id)
    with open(os.path.join(output_dir, "analysis.txt"), "w", encoding="utf-8") as f:
        f.write(analysis)
    print(f"  Analysis saved to: {os.path.join(output_dir, 'analysis.txt')}")

    infographic_path = await generate_infographic(notebook_id, output_dir)

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"  Time elapsed: {elapsed:.0f} seconds")
    print(f"  Notebook ID:  {notebook_id}")
    print(f"  Output files:")
    print(f"    - {meta_path}")
    print(f"    - {os.path.join(output_dir, 'analysis.txt')}")
    print(f"    - {infographic_path}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Full Research Pipeline: YouTube -> NotebookLM -> Infographic")
    parser.add_argument("topic", help="Research topic to search on YouTube")
    parser.add_argument("-n", "--count", type=int, default=25, help="Number of YouTube videos (default: 25)")
    parser.add_argument("-o", "--output", default="./output", help="Output directory (default: ./output)")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.topic, args.count, args.output))


if __name__ == "__main__":
    main()
