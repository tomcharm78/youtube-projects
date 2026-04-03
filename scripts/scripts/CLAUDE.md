  # YouTube Projects — Claude Code Instructions

## Custom Skills

This project has two custom research pipeline skills:

### `/yt-research` — YouTube Research
Searches YouTube for videos on a topic and returns structured metadata (title, URL, author, views, duration).
- Script: `scripts/yt_research.py`
- Dependency: `yt-dlp`
- **If the user does not specify a topic, always ask before proceeding.**

### `/notebooklm` — NotebookLM Integration
Creates Google NotebookLM notebooks, uploads sources (YouTube URLs), runs analysis, and generates deliverables.
- Script: `scripts/notebooklm_tool.py`
- CLI: `notebooklm` (installed via `notebooklm-py`)
- Dependency: `notebooklm-py[browser]`, `playwright`
- **Requires authentication:** user must run `notebooklm login` in a separate terminal first.

## Combined Research Pipeline

When the user requests a full research pipeline (e.g. "find videos on X and send to NotebookLM"):

1. Use `yt-research` to search YouTube for the requested topic and number of videos
2. Present a summary of found videos to the user
3. Use `notebooklm` to create a notebook, upload the YouTube URLs as sources
4. Ask NotebookLM for analysis of the sources
5. Generate any requested deliverables (infographic, slides, flashcards, etc.)
6. Download artifacts to `./output/`

## Output Directory

Generated artifacts (infographics, slides, etc.) are saved to `./output/`.
