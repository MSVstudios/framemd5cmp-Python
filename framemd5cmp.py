#!/usr/bin/env python3
"""framemd5cmp Python port of Bash script.

Usage:
  python -m framemd5cmp <file1> <file2>

This mirrors framemd5cmp behavior:
- dependency checks for ffmpeg/ffprobe
- validate input files and video streams
- generate framemd5 files with ffmpeg
- produce hash-only lists and unified diff
- fails cleanly with status codes
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
from pathlib import Path

DEPENDENCIES = ["ffmpeg", "ffprobe"]


def find_dependency(name: str) -> Path | None:
    path = shutil.which(name)
    return Path(path) if path is not None else None


def ensure_dependencies() -> None:
    missing = [d for d in DEPENDENCIES if find_dependency(d) is None]
    if missing:
        print("Error: missing dependencies:", ", ".join(missing), file=sys.stderr)
        print("Please install ffmpeg and ffprobe and ensure they are in PATH.")
        sys.exit(1)


def is_video_file(path: Path) -> bool:
    cmd = ["ffprobe", "-v", "error", "-show_streams", "-select_streams", "v", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False
    return "index=" in result.stdout


def generate_framemd5(source: Path, output: Path) -> None:
    cmd = [
        "ffmpeg",
        "-n",
        "-i",
        str(source),
        "-an",
        "-map",
        "0:v:0",
        "-f",
        "framemd5",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running ffmpeg for '{source}':", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


def extract_hashonly(framemd5_path: Path, hashonly_path: Path) -> None:
    with framemd5_path.open("r", encoding="utf-8", errors="replace") as fr:
        lines = [line.strip() for line in fr if line.strip() and not line.startswith("#")]

    hashes = []
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            hashes.append(parts[5])

    with hashonly_path.open("w", encoding="utf-8") as fw:
        fw.write("\n".join(hashes))
        if hashes:
            fw.write("\n")


def run_diff(hash1: Path, hash2: Path, out_diff: Path) -> int:
    text1 = hash1.read_text(encoding="utf-8").splitlines(keepends=True)
    text2 = hash2.read_text(encoding="utf-8").splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(text1, text2, fromfile=str(hash1), tofile=str(hash2)))
    out_diff.write_text("".join(diff_lines), encoding="utf-8")
    return 0 if not diff_lines else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="framemd5cmp Python version")
    parser.add_argument("file1", help="First video file")
    parser.add_argument("file2", help="Second video file")
    return parser.parse_args()


def main() -> int:
    ensure_dependencies()
    args = parse_args()

    file1 = Path(args.file1).expanduser().resolve()
    file2 = Path(args.file2).expanduser().resolve()

    if file1 == file2:
        print("Error: files must be different", file=sys.stderr)
        return 2

    for f in (file1, file2):
        if not f.is_file() or f.stat().st_size == 0:
            print(f"Error: '{f}' must be an existing non-empty file", file=sys.stderr)
            return 2

    if not is_video_file(file1):
        print(f"Error: {file1} is not a video file (as recognized by ffprobe).", file=sys.stderr)
        return 3
    if not is_video_file(file2):
        print(f"Error: {file2} is not a video file (as recognized by ffprobe).", file=sys.stderr)
        return 3

    output_dir = Path(".").resolve()

    name1 = file1.stem
    name2 = file2.stem
    if name1 == name2:
        name1 += "_1"
        name2 += "_2"

    framemd5_1 = output_dir / f"{name1}_framemd5.txt"
    framemd5_2 = output_dir / f"{name2}_framemd5.txt"
    hashonly_1 = output_dir / f"{name1}_hashonly.txt"
    hashonly_2 = output_dir / f"{name2}_hashonly.txt"
    diff_file = output_dir / f"{name1}_vs_{name2}_diff.txt"

    generate_framemd5(file1, framemd5_1)
    generate_framemd5(file2, framemd5_2)
    extract_hashonly(framemd5_1, hashonly_1)
    extract_hashonly(framemd5_2, hashonly_2)
    diff_status = run_diff(hashonly_1, hashonly_2, diff_file)

    print(f"framemd5 file: {framemd5_1}")
    print(f"framemd5 file: {framemd5_2}")
    print(f"hash-only: {hashonly_1}")
    print(f"hash-only: {hashonly_2}")
    print(f"diff: {diff_file}")

    return diff_status


if __name__ == "__main__":
    raise SystemExit(main())
