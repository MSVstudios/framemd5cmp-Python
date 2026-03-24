# framemd5cmp-Python

Porting of the original `framemd5cmp` (https://github.com/bavc/framemd5cmp) Bash tool to Python. The purpose is the same:
compare video files frame-by-frame using `framemd5` output hashes and report differences.

## Project structure

- `framemd5cmp.py`: compare two video files by generating frame MD5 (framemd5) for each, extracting hash-only file and diffing.
- `makeframemd5.py`: generate framemd5 files from a single source with options (decode, copy codec, or filtered fingerprint).
- `tests/*`: pytest tests for behavior and dependency checks.

## Behavior overview

### framemd5cmp.py

- Purpose: verify frame-level equality (decoded pixel hash) between two inputs.
- Steps:
  1. verify `ffmpeg`/`ffprobe` availability via `shutil.which`.
  2. validate input files exist, are non-empty, and are different paths.
  3. confirm video streams with `ffprobe -show_streams -select_streams v`.
  4. create `<base>_framemd5.txt` with `ffmpeg -f framemd5`.
  5. extract hash values into `<base>_hashonly.txt`.
  6. diff hash files via `difflib.unified_diff` into `<base1>_vs_<base2>_diff.txt`.
  7. exit status indicates no difference (`0`), differences (`1`), or error codes.

### makeframemd5.py

- Purpose: create reliable measurable frame hash outputs for a single input, optionally with transformations.
- Modes:
  - `-d`: decoded framemd5 (default for `makeframemd5` behavior).
  - `-c`: codec copy + framemd5 (packet-level copy path).
  - `-f`: filtered, normalized fingerprint (monochrome+scale) for robust comparison.
- `--force`: overwrite existing outputs.
- path decisions:
  - file input → output at `<input_dir>/framemd5/`.
  - directory input → output at `<input_dir>/metadata/submissionDocumentation/framemd5/`.
- handles FFREPORT path to avoid `file=D` bug on Windows.

## Requirements

- Python 3.10+ (for `Path` and typing syntax).
- `ffmpeg` available in `PATH`.
- `ffprobe` available in `PATH`.

## framemd5cmp.py usage

```bash
python -m framemd5cmp <file1> <file2>
```

Behavior:

1. checks `ffmpeg`/`ffprobe` with `shutil.which`.
2. validates both inputs exist and have non-zero size.
3. rejects identical paths.
4. validates each is a video stream with `ffprobe -show_streams -select_streams v`.
5. generates `*.framemd5` files:
   - `<basename>_framemd5.txt`
6. extracts hash column to `<basename>_hashonly.txt`.
7. diff via `difflib.unified_diff` into `<base1>_vs_<base2>_diff.txt`.

Exit codes:

- `0` - no differences.
- `1` - differences found.
- `2` - input validation error.
- `3` - video validation failure, also others depending on ffmpeg exit code.

### Key options
No extra CLI options beyond the two positional files.

## makeframemd5.py usage

```bash
python -m makeframemd5 -i <input-file> [-d] [-c] [-f] [--force] [--version]
```

Options:

- `-i`, `--input`: required; file path (or directory) to process.
- `-d`: decode video frames before checksum; output `<base>_framemd5.md5`.
- `-c`: copy codec stream (no re-encode) to framemd5; output `<base>_codec_copy_framemd5.md5`.
- `-f`: experimental filter (monochrome & scale) to framemd5; output `<base>_monow_sqcif_framemd5.md5`.
- `--force`: overwrite existing output files.
- `--version`: print version and exit.

Output path policy:

- if input is a file: output directory is `<input_dir>/framemd5`.
- if input is a directory: output directory is `<input_dir>/metadata/submissionDocumentation/framemd5`.

Logging policy (FFREPORT):

- FFREPORT is set to a per-input log file under `logs/` within output directory.
- escaping for Windows path drive letter MUST be handled when using `FFREPORT` to avoid ffmpeg interpreting `file=D`.
  - e.g.: `ffmpeg_env['FFREPORT'] = f"file={(log_dir / log_name).as_posix().replace(':', '\\:')}"`.
- alternative safe approach: do not rely on FFREPORT; capture stdout/stderr in Python and write log file manually.

### Problem note

The legacy issue in this repo observed a weird `D` file creation.
<br>Cause:
FFREPORT with Windows absolute path produced `file=D:\...`, ffmpeg parsed as `file=D` and created file `D` in current folder.

### Robust fix

- use `cwd=log_dir` in `subprocess.run` and set `FFREPORT` to filename only, e.g. `file=framemd5.log`.
- or omit FFREPORT entirely and do:

```python
r = subprocess.run(cmd, capture_output=True, text=True)
(log_dir / 'ffmpeg.log').write_text(r.stdout + '\n' + r.stderr)
```

## Automatic tests (pytest)

`tests/test_makeframemd5.py` verifies:

- default behavior generates one request
- flags generate expected output names
- `--force` deletes existing file and proceeds

`tests/test_framemd5cmp.py` verifies:

- dependency check on `ffmpeg`/`ffprobe`
- `is_video_file` semantics for success/failure paths using mocked `subprocess.run`

## Example workflow

1. Generate framemd5 from two files (anonymized names):

```bash
python -m makeframemd5 -i "data/sample_video_copy.mp4" --force
python -m makeframemd5 -i "data/sample_video.mp4" --force
```

2. Compare:

```bash
python -m framemd5cmp "data/sample_video_copy.mp4" "data/sample_video.mp4"
```

3. Inspect outputs:

- `data/framemd5/sample_video_copy_framemd5.md5`
- `data/framemd5/sample_video_copy_hashonly.txt`
- `data/framemd5/sample_video_copy_vs_sample_video_diff.txt`

## Notes

- It's critical to quote paths with spaces in PowerShell and cmd.
- Keep ffmpeg and ffprobe in PATH (local environment install, e.g. choco/brew).
- For large files, execution can be slow due to per-frame hashing and no incremental caches.

## Contribution

Pull requests accepted for:

- better CLI args parser (argparse enhancements)
- support for output directory override
- multithreaded plan for huge batch run
- custom diff threshold (perceptual difference vs exact frame equality)

---

Maintainer: [MSV studios]

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.




