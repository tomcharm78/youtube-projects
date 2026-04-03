#!/usr/bin/env python3
"""NotebookLM Tool - wraps the notebooklm-py client for use as a Claude Code skill."""

import argparse
import asyncio
import json
import sys

from notebooklm import NotebookLMClient


async def create_notebook(name):
    """Create a new notebook and return its id."""
    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(name)
        return {"notebook_id": nb.id, "name": name, "status": "created"}


async def add_youtube_sources(notebook_id, urls):
    """Add YouTube URLs as sources to an existing notebook."""
    results = []
    async with await NotebookLMClient.from_storage() as client:
        for url in urls:
            try:
                await client.sources.add_url(notebook_id, url, wait=True)
                results.append({"url": url, "status": "added"})
            except Exception as e:
                results.append({"url": url, "status": "error", "error": str(e)})
    return results


async def ask_notebook(notebook_id, question):
    """Ask a question against the notebook sources."""
    async with await NotebookLMClient.from_storage() as client:
        result = await client.chat.ask(notebook_id, question)
        return {"question": question, "answer": result.answer}


async def generate_artifact(notebook_id, artifact_type, **kwargs):
    """Generate a content artifact (infographic, slide-deck, flashcards, etc.)."""
    async with await NotebookLMClient.from_storage() as client:
        gen_map = {
            "infographic": client.artifacts.generate_infographic,
            "slide-deck": client.artifacts.generate_slide_deck,
            "flashcards": client.artifacts.generate_flashcards,
            "quiz": client.artifacts.generate_quiz,
            "audio": client.artifacts.generate_audio,
            "video": client.artifacts.generate_video,
            "mind-map": client.artifacts.generate_mind_map,
            "data-table": client.artifacts.generate_data_table,
        }

        gen_fn = gen_map.get(artifact_type)
        if gen_fn is None:
            return {"error": f"Unknown artifact type: {artifact_type}. Supported: {list(gen_map.keys())}"}

        call_kwargs = {}
        if kwargs.get("instructions"):
            call_kwargs["instructions"] = kwargs["instructions"]
        if kwargs.get("style"):
            call_kwargs["style"] = kwargs["style"]
        if kwargs.get("orientation"):
            call_kwargs["orientation"] = kwargs["orientation"]

        status = await gen_fn(notebook_id, **call_kwargs)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        return {"artifact": artifact_type, "status": "completed", "task_id": status.task_id}


async def download_artifact(notebook_id, artifact_type, output_path, **kwargs):
    """Download a previously generated artifact to a local file."""
    async with await NotebookLMClient.from_storage() as client:
        dl_map = {
            "infographic": client.artifacts.download_infographic,
            "slide-deck": client.artifacts.download_slide_deck,
            "flashcards": client.artifacts.download_flashcards,
            "quiz": client.artifacts.download_quiz,
            "audio": client.artifacts.download_audio,
            "video": client.artifacts.download_video,
            "mind-map": client.artifacts.download_mind_map,
            "data-table": client.artifacts.download_data_table,
        }

        dl_fn = dl_map.get(artifact_type)
        if dl_fn is None:
            return {"error": f"Unknown artifact type: {artifact_type}"}

        dl_kwargs = {}
        if kwargs.get("output_format"):
            dl_kwargs["output_format"] = kwargs["output_format"]

        await dl_fn(notebook_id, output_path, **dl_kwargs)
        return {"artifact": artifact_type, "output_path": output_path, "status": "downloaded"}


def main():
    parser = argparse.ArgumentParser(description="NotebookLM tool for Claude Code")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new notebook")
    p_create.add_argument("name", help="Notebook name")

    p_add = sub.add_parser("add-sources", help="Add YouTube URLs as sources")
    p_add.add_argument("notebook_id", help="Notebook ID")
    p_add.add_argument("urls", nargs="+", help="YouTube URLs to add")

    p_ask = sub.add_parser("ask", help="Ask a question")
    p_ask.add_argument("notebook_id", help="Notebook ID")
    p_ask.add_argument("question", help="Question to ask")

    p_gen = sub.add_parser("generate", help="Generate an artifact")
    p_gen.add_argument("notebook_id", help="Notebook ID")
    p_gen.add_argument("artifact_type", help="Type: infographic, slide-deck, flashcards, quiz, audio, video, mind-map, data-table")
    p_gen.add_argument("--instructions", default=None, help="Optional generation instructions")
    p_gen.add_argument("--style", default=None, help="Optional style (e.g. whiteboard, chalkboard)")
    p_gen.add_argument("--orientation", default=None, help="Optional orientation (portrait/landscape)")

    p_dl = sub.add_parser("download", help="Download an artifact")
    p_dl.add_argument("notebook_id", help="Notebook ID")
    p_dl.add_argument("artifact_type", help="Artifact type to download")
    p_dl.add_argument("output_path", help="Local file path for the download")
    p_dl.add_argument("--format", dest="output_format", default=None, help="Output format (json, markdown, csv)")

    args = parser.parse_args()

    if args.command == "create":
        result = asyncio.run(create_notebook(args.name))
    elif args.command == "add-sources":
        result = asyncio.run(add_youtube_sources(args.notebook_id, args.urls))
    elif args.command == "ask":
        result = asyncio.run(ask_notebook(args.notebook_id, args.question))
    elif args.command == "generate":
        result = asyncio.run(generate_artifact(
            args.notebook_id, args.artifact_type,
            instructions=args.instructions, style=args.style, orientation=args.orientation
        ))
    elif args.command == "download":
        result = asyncio.run(download_artifact(
            args.notebook_id, args.artifact_type, args.output_path,
            output_format=args.output_format
        ))
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
