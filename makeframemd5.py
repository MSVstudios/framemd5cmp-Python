#!/usr/bin/env python3
"""makeframemd5 Python port of Bash script."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEPENDENCIES = ["ffmpeg", "ffprobe"]
VERSION = "1.0"


def find_dependency(name: str) -> Path | None:
    path = shutil.which(name)
    return Path(path) if path is not None else None


def ensure_dependencies() -> None:
    missing = [d for d in DEPENDENCIES if find_dependency(d) is None]
    if missing:
        print("This script requires the following dependencies to run but they are not installed:", ", ".join(missing), file=sys.stderr)
        print("Please install the missing commands and ensure they are in PATH.", file=sys.stderr)
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # Usa Path come type per normalizzare subito l'input
    parser.add_argument("-i", "--input", type=Path, required=True, help="Input file path")
    parser.add_argument("-d", action="store_true", help="Enable 'd' option")
    parser.add_argument("-c", action="store_true", help="Copy video frames to checksum utility")
    parser.add_argument("-f", action="store_true", help="(experimental) fingerprint video frames via format=monow,scale=40:30")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    return parser.parse_args()


def build_output_paths(input_path: Path) -> tuple[Path, Path]:
    if input_path.is_dir():
        output_dir = input_path / "metadata" / "submissionDocumentation" / "framemd5"
        log_dir = output_dir / "logs"
    else:
        output_dir = input_path.parent / "framemd5"
        log_dir = output_dir / "logs"
    return output_dir, log_dir


import argparse
from pathlib import Path

def build_options(input_path: Path, output_dir: Path, args: argparse.Namespace) -> list[list[str]]:
    requests: list[list[str]] = []
    
    # Normalizzazione assoluta per evitare problemi con i backslash di Windows
    input_path = input_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = output_dir.resolve()
    
    base_name = input_path.stem

    def add_if_missing(out_file: Path, ffmpeg_opts: list[str]) -> None:
        if out_file.exists():
            if not args.force:
                print(f"Skipping: {out_file.name} already exists.")
                return
            else:
                out_file.unlink()
                print(f"Overwriting: {out_file.name}")

        # COSTRUZIONE LISTA: Solo gli argomenti, senza il binario 'ffmpeg'
        # Usiamo str() solo qui per la compatibilità con subprocess
        cmd = ["-i", str(input_path)] + ffmpeg_opts + [str(out_file)]
        requests.append(cmd)

    # Definizione dei task
    if args.d or not (args.d or args.c or args.f):
        add_if_missing(output_dir / f"{base_name}_framemd5.md5", ["-an", "-f", "framemd5"])

    if args.c:
        add_if_missing(output_dir / f"{base_name}_codec_copy_framemd5.md5", ["-c:v", "copy", "-an", "-f", "framemd5"])

    if args.f:
        # Nota: -vsync è deprecato, meglio non metterlo o usare -fps_mode passthrough se serve
        add_if_missing(output_dir / f"{base_name}_monow_sqcif_framemd5.md5", 
                       ["-vf", "format=monow,scale=40:30", "-an", "-f", "framemd5"])

    return requests


def run_ffmpeg(request: list[str], ffmpeg_env: dict[str, str], cwd: Path | None = None) -> int:
    cmd = ["ffmpeg"] + request
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=ffmpeg_env, cwd=str(cwd) if cwd is not None else None)
    if result.returncode != 0:
        print(f"ffmpeg failed (exit {result.returncode})", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    return result.returncode


def main() -> int:
    ensure_dependencies()
    args = parse_args()

    if args.version:
        print(f"makeframemd5 version {VERSION}")
        return 0

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print("Error: input path does not exist", file=sys.stderr)
        return 1

    if input_path.is_dir():
        # no further check for directory contents, script supports directory for output path only
        pass
    else:
        if not input_path.is_file():
            print("Sorry, the input must be a file (for now).", file=sys.stderr)
            return 1

    output_dir, log_dir = build_output_paths(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_env = os.environ.copy()
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        # Use only the log file name in FFREPORT to avoid colon (:) parsing issues on Windows
        log_filename = f"{input_path.stem}_%p_%t_makeframemd5_{VERSION}.txt"
        ffmpeg_env["FFREPORT"] = f"file={log_filename}"
        input_options = ["-vsync", "passthrough", "-v", "warning", "-stats"]
    else:
        input_options = []

    requests = build_options(input_path, output_dir, args)
    if not requests:
        print("No output frames options to run, exiting.")
        return 0

    exit_code = 0
    for request in requests:
        cmd_request = input_options + request
        code = run_ffmpeg(cmd_request, ffmpeg_env, cwd=log_dir)
        if code != 0:
            exit_code = code

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
